import os
import subprocess
import sys

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.database.session import get_db
from app.main import app
from app.models import Base, PracticeExam, User
from app.repositories.exam import practice_exam_repo
from app.tests.conftest import bearer, login


def test_migrations_match_models_and_preserve_legacy_accounts(db_engine):
    config = Config("alembic.ini")
    with db_engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "0001")
        connection.execute(text("INSERT INTO users(username,password_hash,role) VALUES ('legacy','unchanged-hash','Student')"))
        command.upgrade(config, "head")
        row = connection.execute(text("SELECT full_name,is_active,password_hash FROM users WHERE username='legacy'")).one()
        assert tuple(row) == ("legacy", True, "unchanged-hash")
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        command.downgrade(config, "base")
        assert set(inspect(connection).get_table_names()) == {"alembic_version"}
        command.upgrade(config, "head")


def test_cli_creates_teacher_without_overwriting_existing_account(db_engine, db):
    env = {**os.environ, "DATABASE_URL": str(db_engine.url.render_as_string(hide_password=False)),
           "PGOPTIONS": f"-csearch_path={db_engine.test_schema}", "SEED_TEACHER_PASSWORD": "seed-password"}
    args = [sys.executable, "-m", "app.cli.seed_teacher", "--username", "seed_teacher", "--full-name", "Cô giáo"]
    result = subprocess.run(args, env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "seed-password" not in result.stdout
    assert db.query(User).filter_by(username="seed_teacher").one().role == "Teacher"
    result = subprocess.run(args, env=env, text=True, capture_output=True)
    assert result.returncode != 0
    assert db.query(User).filter_by(username="seed_teacher").count() == 1
    invalid = subprocess.run(args, env={**env, "SEED_TEACHER_PASSWORD": "short"}, text=True, capture_output=True)
    assert invalid.returncode != 0
    assert "short" not in invalid.stdout + invalid.stderr


def test_cors_and_health(client):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    for origin, allowed in (("http://localhost:3000", True), ("https://untrusted.example", False)):
        response = client.options("/api/v1/auth/login", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        assert (response.headers.get("access-control-allow-origin") == origin) is allowed


def test_readiness_returns_503_without_database_details(client):
    class BrokenDB:
        def execute(self, _):
            raise OperationalError("SELECT secret", {}, RuntimeError("password=hidden"))
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = lambda: BrokenDB()
    try:
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert "hidden" not in response.text and "SELECT" not in response.text
        assert client.get("/health/live").status_code == 200
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous


def test_request_rolls_back_after_repository_flush(client, db, accounts, monkeypatch):
    headers = bearer(login(client, "teacher_one"))
    original = practice_exam_repo.create_with_teacher
    def failing(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("failure after flushing exam and questions")
    monkeypatch.setattr(practice_exam_repo, "create_with_teacher", failing)
    response = client.post("/api/v1/exams/practice", headers=headers,
                           json={"title": "must rollback", "questions": [{"content": "Q", "max_score": .8}] * 5})
    assert response.status_code == 500
    assert "flushing" not in response.text
    assert db.query(PracticeExam).filter_by(title="must rollback").count() == 0


def test_production_rejects_default_secret_and_wildcard_cors():
    import pytest
    with pytest.raises(ValueError):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="supersecretkey_please_change_in_production")
    with pytest.raises(ValueError):
        Settings(_env_file=None, CORS_ORIGINS=["*"])
