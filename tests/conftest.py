"""
Tests run against a throwaway sqlite file, never the real MySQL database.
The DATABASE_URL env var is hijacked *before* anything in `app` is imported,
since app.database builds its engine at import time from app.config.settings.
sqlite is fine here: nothing in the models/queries is MySQL-specific (verified
by hand against a real MySQL 8 instance when this app was ported to it).
"""

import os
import tempfile
import uuid
from pathlib import Path

import pytest

_TEST_DB_PATH = Path(tempfile.gettempdir()) / f"attendance_test_{uuid.uuid4().hex}.sqlite"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Activity, User  # noqa: E402
from app.security import create_access_token, hash_password  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_db():
    """Every test starts from an empty schema; tables already exist (created at import time)."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(scope="session", autouse=True)
def _remove_test_db_file():
    yield
    engine.dispose()
    _TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def register_user(client):
    """Self-registers a user (must_change_password=False) and returns (user, token, auth_headers)."""

    def _register(name="Ana Perez", email="ana@example.com", password="password123"):
        resp = client.post(
            "/api/register",
            json={"name": name, "email": email, "password": password, "password_confirmation": password},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        headers = {"Authorization": f"Bearer {data['token']}"}
        return data["user"], data["token"], headers

    return _register


@pytest.fixture
def bulk_user():
    """Directly inserts a user the way an out-of-band import would: a generated
    password and must_change_password=True, bypassing the API entirely."""

    def _bulk_user(name="Bulk Host", email="bulk@example.com", password="TempPass123"):
        db = SessionLocal()
        try:
            user = User(name=name, email=email, hashed_password=hash_password(password), must_change_password=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            token = create_access_token(user.id)
            return user, token, {"Authorization": f"Bearer {token}"}
        finally:
            db.close()

    return _bulk_user


@pytest.fixture
def make_activity():
    """Directly inserts an activity, sidestepping the authenticated create-activity endpoint."""

    def _make_activity(host_id, title="Taller de Prueba", subject="Programación", **kwargs):
        db = SessionLocal()
        try:
            activity = Activity(title=title, subject=subject, host_id=host_id, **kwargs)
            db.add(activity)
            db.commit()
            db.refresh(activity)
            return activity
        finally:
            db.close()

    return _make_activity
