from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import utcnow, verify_password
from app.models import AuthSession, User
from app.tests.conftest import bearer, login

REGISTER = {"username": "new_student", "password": "student-password", "full_name": "Nguyễn Văn An",
            "school_name": "THCS Yên Phong"}


def test_registration_hashes_password_and_has_safe_defaults(client, db):
    response = client.post("/api/v1/auth/register", json=REGISTER)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["role"] == "Student" and data["class_id"] is None and data["is_active"] is True
    assert data["full_name"] == REGISTER["full_name"] and data["school_name"] == REGISTER["school_name"]
    assert "password" not in data and "password_hash" not in data
    user = db.query(User).filter_by(username=REGISTER["username"]).one()
    assert user.password_hash != REGISTER["password"]
    assert verify_password(REGISTER["password"], user.password_hash)
    tokens = login(client, REGISTER["username"], REGISTER["password"])
    assert client.get("/api/v1/auth/me", headers=bearer(tokens)).json()["id"] == data["id"]


@pytest.mark.parametrize("extra", [{"role": "Teacher"}, {"class_id": 1}, {"is_active": True}])
def test_public_registration_cannot_choose_privileges(client, extra):
    response = client.post("/api/v1/auth/register", json={**REGISTER, **extra})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert REGISTER["password"] not in response.text


@pytest.mark.parametrize("change", [{"username": "bad name"}, {"full_name": " "},
                                     {"password": "short"}, {"password": "á" * 37}])
def test_registration_validates_fields_without_echoing_secrets(client, change):
    response = client.post("/api/v1/auth/register", json={**REGISTER, **change})
    assert response.status_code == 422
    assert "input" not in response.json()["error"]["details"][0]


def test_duplicate_username_is_conflict_not_server_error(client):
    assert client.post("/api/v1/auth/register", json=REGISTER).status_code == 201
    response = client.post("/api/v1/auth/register", json=REGISTER)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_teacher_creation_is_not_a_public_endpoint(client):
    assert client.post("/api/v1/users/teachers", json=REGISTER).status_code == 404


def test_login_errors_are_generic_and_missing_token_is_unauthorized(client, accounts):
    responses = [client.post("/api/v1/auth/login", data={"username": u, "password": "wrong-password"})
                 for u in ("student_one", "missing-user")]
    assert responses[0].status_code == responses[1].status_code == 401
    assert responses[0].json() == responses[1].json()
    assert responses[0].headers["www-authenticate"] == "Bearer"
    assert client.get("/api/v1/auth/me").status_code == 401


def test_refresh_rotates_and_logout_revokes_current_session(client, db, accounts):
    original = login(client)
    second_session = login(client)
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    replacement = response.json()
    assert replacement["refresh_token"] != original["refresh_token"]
    assert db.query(AuthSession).filter_by(refresh_token_hash=replacement["refresh_token"]).first() is None
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}).status_code == 401
    assert client.post("/api/v1/auth/logout", headers=bearer(replacement)).status_code == 204
    assert client.get("/api/v1/auth/me", headers=bearer(original)).status_code == 401
    assert client.get("/api/v1/auth/me", headers=bearer(replacement)).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": replacement["refresh_token"]}).status_code == 401
    assert client.get("/api/v1/auth/me", headers=bearer(second_session)).status_code == 200


def test_concurrent_refresh_has_exactly_one_winner(client, accounts):
    tokens = login(client)
    def refresh(_):
        return client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(refresh, range(2)))
    assert sorted(r.status_code for r in responses) == [200, 401]
    winning = next(r.json() for r in responses if r.status_code == 200)
    assert client.get("/api/v1/auth/me", headers=bearer(winning)).status_code == 200


def test_password_change_revokes_every_session_and_requires_old_password(client, accounts):
    first, second = login(client), login(client)
    body = {"current_password": "incorrect", "new_password": "replacement-password"}
    assert client.put("/api/v1/auth/password", headers=bearer(first), json=body).status_code == 400
    assert client.get("/api/v1/auth/me", headers=bearer(first)).status_code == 200
    body["current_password"] = "initial-password"
    assert client.put("/api/v1/auth/password", headers=bearer(first), json=body).status_code == 204
    for token in (first, second):
        assert client.get("/api/v1/auth/me", headers=bearer(token)).status_code == 401
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": token["refresh_token"]}).status_code == 401
    assert client.post("/api/v1/auth/login", data={"username": "student_one", "password": "initial-password"}).status_code == 401
    assert login(client, password="replacement-password")


def test_inactive_account_cannot_login_refresh_or_access(client, db, accounts):
    tokens = login(client)
    accounts["student_one"].is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=bearer(tokens)).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post("/api/v1/auth/login", data={"username": "student_one", "password": "initial-password"}).status_code == 401


def test_expired_session_and_tampered_token_are_rejected(client, db, accounts):
    tokens = login(client)
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad-token"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + tokens["refresh_token"]}).status_code == 401
    payload = jwt.decode(tokens["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM], audience=settings.TOKEN_AUDIENCE)
    for changes in ({"exp": utcnow() - timedelta(seconds=1)}, {"aud": "other"}, {"type": "refresh"}, {"sub": "999999"}):
        invalid = jwt.encode({**payload, **changes}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + invalid}).status_code == 401
    session = db.query(AuthSession).one()
    session.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/v1/auth/me", headers=bearer(tokens)).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
