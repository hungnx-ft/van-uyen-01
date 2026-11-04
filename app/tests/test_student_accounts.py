import pytest

from app.models import Class, User
from app.services.user import student_username_base
from app.tests.conftest import bearer, login

DEFAULT = "123456"


@pytest.fixture
def classroom(db, accounts):
    room = Class(name="9A", teacher_id=accounts["teacher_one"].id)
    db.add(room)
    db.commit()
    return room


def _teacher(client):
    return bearer(login(client, "teacher_one"))


def _create(client, headers, classroom, full_name="Nguyễn Văn An", **extra):
    return client.post("/api/v1/users/students", headers=headers,
                       json={"full_name": full_name, "class_id": classroom.id, **extra})


@pytest.mark.parametrize("name,expected", [
    ("Nguyễn Văn An", "nguyenvanan"),
    ("Đặng Thị Đào", "dangthidao"),
    ("  TRẦN   Ngọc-Ánh  ", "tranngocanh"),
    ("Lê Văn Bảy 2", "levanbay2"),
    ("李小龙", "hocsinh"),
    ("😀", "hocsinh"),
    ("A" * 80, "a" * 40),
])
def test_username_base_strips_vietnamese_marks(name, expected):
    assert student_username_base(name) == expected


def test_created_student_gets_generated_username_and_default_password(client, db, classroom):
    headers = _teacher(client)
    # Client-supplied credentials are ignored.
    response = _create(client, headers, classroom, username="chosen", password="chosen-password")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["username"] == f"hs_nguyenvanan_{body['id']}"
    assert body["temporary_password"] == DEFAULT
    assert body["must_change_password"] is True
    assert response.headers["Cache-Control"] == "no-store"
    assert db.query(User).filter_by(username="chosen").first() is None
    assert client.post("/api/v1/auth/login", data={"username": "chosen", "password": "chosen-password"}).status_code == 401
    assert login(client, body["username"], DEFAULT)


def test_same_full_names_get_distinct_usernames(client, classroom):
    headers = _teacher(client)
    first = _create(client, headers, classroom).json()
    second = _create(client, headers, classroom).json()
    assert first["username"] != second["username"]
    assert second["username"] == f"hs_nguyenvanan_{second['id']}"


def test_generated_username_avoids_existing_account(client, db, classroom):
    headers = _teacher(client)
    probe = _create(client, headers, classroom, "Probe").json()
    # The squatter row takes id probe+1, so the next student gets probe+2.
    taken = f"hs_an_{probe['id'] + 2}"
    db.add(User(username=taken, password_hash="x", full_name="Squatter", role="Student"))
    db.commit()
    created = _create(client, headers, classroom, "An").json()
    assert created["id"] == probe["id"] + 2
    assert created["username"] == f"{taken}_2"
    assert login(client, created["username"], DEFAULT)


def test_registration_cannot_use_reserved_prefixes(client, accounts):
    for username in ("hs_nguyenvanan_1", "HS_abc", "tmp_abc"):
        response = client.post("/api/v1/auth/register",
                               json={"username": username, "password": "password-123", "full_name": "X"})
        assert response.status_code == 422, username
    ok = client.post("/api/v1/auth/register",
                     json={"username": "self_made", "password": "password-123", "full_name": "X"})
    assert ok.status_code == 201
    assert ok.json()["must_change_password"] is False


def test_bulk_import_generates_accounts_per_class(client, db, classroom, accounts):
    headers = _teacher(client)
    response = client.post("/api/v1/users/students/bulk", headers=headers, json={
        "class_id": classroom.id,
        "students": [
            {"full_name": "Phạm Minh Châu", "school_name": "THCS A"},
            {"full_name": "Phạm Minh Châu"},
            {"full_name": "Vũ Hà", "username": "ignored", "password": "ignored-password"},
        ],
    })
    assert response.status_code == 201, response.text
    created = response.json()["created"]
    assert response.json()["failed"] == []
    assert [s["username"] for s in created] == [f"hs_phamminhchau_{created[0]['id']}",
                                                 f"hs_phamminhchau_{created[1]['id']}",
                                                 f"hs_vuha_{created[2]['id']}"]
    assert {s["temporary_password"] for s in created} == {DEFAULT}
    assert all(s["class_id"] == classroom.id and s["must_change_password"] for s in created)
    assert created[0]["school_name"] == "THCS A"

    other = Class(name="Khác", teacher_id=accounts["teacher_two"].id)
    db.add(other)
    db.commit()
    foreign = client.post("/api/v1/users/students/bulk", headers=headers,
                          json={"class_id": other.id, "students": [{"full_name": "X"}]})
    assert foreign.status_code == 404


def test_bulk_import_reports_invalid_rows(client, classroom):
    headers = _teacher(client)
    response = client.post("/api/v1/users/students/bulk", headers=headers, json={
        "class_id": classroom.id, "students": [{"full_name": "   "}]})
    assert response.status_code == 422


def test_first_login_requires_password_change(client, classroom):
    headers = _teacher(client)
    student = _create(client, headers, classroom).json()
    tokens = login(client, student["username"], DEFAULT)
    auth = bearer(tokens)

    me = client.get("/api/v1/auth/me", headers=auth)
    assert me.status_code == 200
    assert me.json()["must_change_password"] is True
    for path in ("/api/v1/theory/", "/api/v1/exams/practice", "/api/v1/exams/mock",
                 "/api/v1/assignments/", "/api/v1/submissions/my-submissions"):
        blocked = client.get(path, headers=auth)
        assert blocked.status_code == 403, path
        assert blocked.json()["error"]["code"] == "password_change_required"
    # Refresh still works so the change screen survives an access-token expiry.
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    auth = bearer(refreshed.json())

    # The default and too-short passwords are rejected; so is reusing the current one.
    for new in (DEFAULT, "short"):
        response = client.put("/api/v1/auth/password", headers=auth,
                              json={"current_password": DEFAULT, "new_password": new})
        assert response.status_code == 422, new
    assert client.put("/api/v1/auth/password", headers=auth,
                      json={"current_password": "wrong-pass", "new_password": "my-new-pass"}).status_code == 400
    assert client.put("/api/v1/auth/password", headers=auth,
                      json={"current_password": DEFAULT, "new_password": "my-new-pass"}).status_code == 204

    # Every session is revoked; the student signs in again with the new password.
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401
    assert client.post("/api/v1/auth/login", data={"username": student["username"], "password": DEFAULT}).status_code == 401
    fresh = bearer(login(client, student["username"], "my-new-pass"))
    assert client.get("/api/v1/auth/me", headers=fresh).json()["must_change_password"] is False
    assert client.get("/api/v1/theory/", headers=fresh).status_code == 200


def test_new_password_must_differ_from_current(client, accounts):
    auth = bearer(login(client))
    response = client.put("/api/v1/auth/password", headers=auth,
                          json={"current_password": "initial-password", "new_password": "initial-password"})
    assert response.status_code == 400


def test_pending_student_can_log_out(client, classroom):
    student = _create(client, _teacher(client), classroom).json()
    auth = bearer(login(client, student["username"], DEFAULT))
    assert client.post("/api/v1/auth/logout", headers=auth).status_code == 204
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401


@pytest.mark.parametrize("method,suffix", [("put", "/password"), ("post", "/password/reset")])
def test_teacher_reset_restores_default_and_forces_change(client, classroom, method, suffix):
    headers = _teacher(client)
    student = _create(client, headers, classroom).json()
    first = bearer(login(client, student["username"], DEFAULT))
    assert client.put("/api/v1/auth/password", headers=first,
                      json={"current_password": DEFAULT, "new_password": "chosen-pass-1"}).status_code == 204
    active = bearer(login(client, student["username"], "chosen-pass-1"))
    assert client.get("/api/v1/theory/", headers=active).status_code == 200

    reset = getattr(client, method)(f"/api/v1/users/students/{student['id']}{suffix}", headers=headers)
    assert reset.status_code == 200, reset.text
    assert reset.json()["temporary_password"] == DEFAULT
    assert reset.json()["must_change_password"] is True
    assert reset.headers["Cache-Control"] == "no-store"

    assert client.get("/api/v1/auth/me", headers=active).status_code == 401
    assert client.post("/api/v1/auth/login",
                       data={"username": student["username"], "password": "chosen-pass-1"}).status_code == 401
    pending = bearer(login(client, student["username"], DEFAULT))
    assert client.get("/api/v1/theory/", headers=pending).status_code == 403
    assert client.put("/api/v1/auth/password", headers=pending,
                      json={"current_password": DEFAULT, "new_password": "chosen-pass-2"}).status_code == 204
    assert client.get("/api/v1/theory/", headers=bearer(login(client, student["username"], "chosen-pass-2"))).status_code == 200


def test_students_and_other_teachers_cannot_reset(client, db, classroom, accounts):
    student = _create(client, _teacher(client), classroom).json()
    for actor, expected in (("teacher_two", 404), ("student_one", 403)):
        headers = bearer(login(client, actor))
        assert client.put(f"/api/v1/users/students/{student['id']}/password", headers=headers).status_code == expected
    db.expire_all()
    assert db.get(User, student["id"]).must_change_password is True


def test_student_list_exposes_password_change_status(client, classroom):
    headers = _teacher(client)
    student = _create(client, headers, classroom).json()
    items = client.get(f"/api/v1/users/students?class_id={classroom.id}", headers=headers).json()["items"]
    row = next(item for item in items if item["id"] == student["id"])
    assert row["must_change_password"] is True
    assert "temporary_password" not in row
