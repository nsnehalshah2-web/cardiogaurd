import os
import sys
import tempfile
import uuid

import pytest

# Point the app at a throwaway database before it is imported.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def register(client) -> dict:
    email = f"{uuid.uuid4().hex[:10]}@test.com"
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User", "email": email, "password": "Test12345!", "confirm_password": "Test12345!",
    })
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth(client):
    return register(client)


@pytest.fixture
def other_auth(client):
    return register(client)
