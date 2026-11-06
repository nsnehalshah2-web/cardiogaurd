from app.main import _get_cors_origins


def test_frontend_origin_is_allowed_when_cors_setting_is_stale(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://old-frontend.example.com")
    monkeypatch.setenv("FRONTEND_URL", "https://nsnehalshah2-web.github.io/Cardioguard/")

    assert _get_cors_origins() == [
        "https://old-frontend.example.com",
        "https://nsnehalshah2-web.github.io",
    ]
