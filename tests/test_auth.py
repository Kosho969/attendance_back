def test_register_creates_user_that_does_not_need_a_password_change(client):
    resp = client.post(
        "/api/register",
        json={
            "name": "Ana Perez",
            "email": "ana@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == "ana@example.com"
    assert body["user"]["must_change_password"] is False
    assert body["token"]


def test_register_rejects_duplicate_email(client, register_user):
    register_user(email="ana@example.com")
    resp = client.post(
        "/api/register",
        json={
            "name": "Other Ana",
            "email": "ana@example.com",
            "password": "password123",
            "password_confirmation": "password123",
        },
    )
    assert resp.status_code == 422
    assert "email" in resp.json()["errors"]


def test_register_rejects_mismatched_password_confirmation(client):
    resp = client.post(
        "/api/register",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "password123",
            "password_confirmation": "somethingelse",
        },
    )
    assert resp.status_code == 422
    assert "password_confirmation" in resp.json()["errors"]


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/register",
        json={"name": "Ana", "email": "ana@example.com", "password": "short", "password_confirmation": "short"},
    )
    assert resp.status_code == 422
    assert "password" in resp.json()["errors"]


def test_login_succeeds_with_correct_credentials(client, register_user):
    register_user(email="ana@example.com", password="password123")
    resp = client.post("/api/login", json={"email": "ana@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "ana@example.com"


def test_login_rejects_wrong_password(client, register_user):
    register_user(email="ana@example.com", password="password123")
    resp = client.post("/api/login", json={"email": "ana@example.com", "password": "wrong-password"})
    assert resp.status_code == 422


def test_login_rejects_unknown_email(client):
    resp = client.post("/api/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 422


def test_me_requires_auth(client):
    assert client.get("/api/user").status_code == 401


def test_me_returns_current_user(client, register_user):
    user, _token, headers = register_user()
    resp = client.get("/api/user", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == user["id"]


def test_bulk_imported_user_is_blocked_from_other_endpoints_until_password_changed(client, bulk_user):
    _user, _token, headers = bulk_user()

    resp = client.get("/api/users", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "password_change_required"

    # GET /user and logout must stay reachable despite the forced-change flag.
    assert client.get("/api/user", headers=headers).status_code == 200
    assert client.post("/api/logout", headers=headers).status_code == 200


def test_change_password_rejects_wrong_current_password(client, bulk_user):
    _user, _token, headers = bulk_user(password="TempPass123")
    resp = client.put(
        "/api/user/password",
        headers=headers,
        json={"current_password": "wrong", "password": "NewPassword123", "password_confirmation": "NewPassword123"},
    )
    assert resp.status_code == 422
    assert "current_password" in resp.json()["errors"]


def test_change_password_clears_forced_flag_and_unlocks_other_endpoints(client, bulk_user):
    _user, _token, headers = bulk_user(password="TempPass123")

    resp = client.put(
        "/api/user/password",
        headers=headers,
        json={
            "current_password": "TempPass123",
            "password": "NewPassword123",
            "password_confirmation": "NewPassword123",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["must_change_password"] is False

    assert client.get("/api/users", headers=headers).status_code == 200

    # Old password no longer works; new one does.
    assert (
        client.post("/api/login", json={"email": _user.email, "password": "TempPass123"}).status_code == 422
    )
    assert (
        client.post("/api/login", json={"email": _user.email, "password": "NewPassword123"}).status_code == 200
    )
