import uuid

from app.main import PAGES_ORIGIN, _get_cors_origins


def test_current_pages_origin_is_allowed_even_with_stale_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://tanishqtiwari1.github.io")
    monkeypatch.setenv("FRONTEND_URL", "https://tanishqtiwari1.github.io/CardioGuard/")

    origins = _get_cors_origins()

    assert PAGES_ORIGIN in origins
    assert f"{PAGES_ORIGIN}/" not in origins
    assert f"{PAGES_ORIGIN}/cardiogaurd" not in origins


def test_pages_login_preflight_and_request_are_cors_enabled(client):
    headers = {
        "Origin": PAGES_ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    preflight = client.options("/api/v1/auth/login", headers=headers)

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == PAGES_ORIGIN
    assert preflight.headers["access-control-allow-credentials"] == "true"
    assert "authorization" in preflight.headers["access-control-allow-headers"].lower()
    assert "content-type" in preflight.headers["access-control-allow-headers"].lower()

    email = f"{uuid.uuid4().hex}@example.com"
    credentials = {"email": email, "password": "Test12345!"}
    registration = client.post(
        "/api/v1/auth/register",
        json={"name": "CORS Test", **credentials, "confirm_password": credentials["password"]},
        headers={"Origin": PAGES_ORIGIN},
    )
    assert registration.status_code == 201
    assert registration.headers["access-control-allow-origin"] == PAGES_ORIGIN

    login = client.post("/api/v1/auth/login", json=credentials, headers={"Origin": PAGES_ORIGIN})
    assert login.status_code == 200
    assert login.headers["access-control-allow-origin"] == PAGES_ORIGIN

    me = client.get(
        "/api/v1/auth/me",
        headers={
            "Origin": PAGES_ORIGIN,
            "Authorization": f"Bearer {login.json()['access_token']}",
        },
    )
    assert me.status_code == 200
    assert me.headers["access-control-allow-origin"] == PAGES_ORIGIN
