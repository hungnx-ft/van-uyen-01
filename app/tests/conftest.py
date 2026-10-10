import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.database import session as database_session
from app.main import app
from app.models import User


@pytest.fixture
def db_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url or "test" not in (make_url(url).database or ""):
        pytest.fail("TEST_DATABASE_URL must point to an isolated PostgreSQL database containing 'test' in its name")
    schema = "stage1_" + uuid4().hex
    control = create_engine(url, isolation_level="AUTOCOMMIT")
    with control.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    engine.test_schema = schema
    try:
        config = Config("alembic.ini")
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        with control.connect() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()


@pytest.fixture
def db(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_engine, monkeypatch):
    # Exercise the real request transaction dependency against the isolated database.
    monkeypatch.setattr(database_session, "SessionLocal",
                        sessionmaker(bind=db_engine, autocommit=False, autoflush=False))
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def accounts(db):
    password_hash = get_password_hash("initial-password")
    users = {}
    for name, role in (("teacher_one", "Teacher"), ("teacher_two", "Teacher"),
                       ("student_one", "Student"), ("student_two", "Student")):
        user = User(username=name, password_hash=password_hash, full_name=name,
                    role=role, is_active=True)
        db.add(user)
        users[name] = user
    db.commit()
    return users


def login(client, username="student_one", password="initial-password"):
    response = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def bearer(tokens):
    return {"Authorization": "Bearer " + tokens["access_token"]}
