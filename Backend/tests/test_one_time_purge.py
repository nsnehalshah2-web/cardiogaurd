def test_purge_requires_token_and_deletes_all_account_access(client, auth, other_auth, monkeypatch):
    monkeypatch.setenv("ONE_TIME_ACCOUNT_PURGE_TOKEN", "local-test-token")
    endpoint = "/api/v1/admin/purge-all-accounts"

    assert client.post(endpoint, headers={"Authorization": "Bearer wrong"}).status_code == 401
    response = client.post(endpoint, headers={"Authorization": "Bearer local-test-token"})

    assert response.status_code == 200
    assert response.json()["deleted_accounts"] >= 2
    assert client.get("/api/v1/auth/me", headers=auth).status_code == 401
    assert client.get("/api/v1/auth/me", headers=other_auth).status_code == 401
