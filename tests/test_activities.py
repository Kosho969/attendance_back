def test_list_activities_requires_auth(client):
    assert client.get("/api/activities").status_code == 401


def test_create_activity(client, register_user):
    user, _token, headers = register_user()
    resp = client.post(
        "/api/activities",
        headers=headers,
        json={"title": "Taller de Prueba", "subject": "Programación", "host_id": user["id"]},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Taller de Prueba"
    assert body["host"]["id"] == user["id"]
    assert body["attendances_count"] == 0
    assert body["qr_token"]


def test_create_activity_rejects_unknown_host(client, register_user):
    _user, _token, headers = register_user()
    resp = client.post(
        "/api/activities",
        headers=headers,
        json={"title": "Taller", "subject": "Tema", "host_id": 999999},
    )
    assert resp.status_code == 422
    assert "host_id" in resp.json()["errors"]


def test_list_activities_orders_newest_first(client, register_user):
    user, _token, headers = register_user()
    first = client.post(
        "/api/activities", headers=headers, json={"title": "First", "subject": "S", "host_id": user["id"]}
    ).json()
    second = client.post(
        "/api/activities", headers=headers, json={"title": "Second", "subject": "S", "host_id": user["id"]}
    ).json()

    resp = client.get("/api/activities", headers=headers)
    ids = [a["id"] for a in resp.json()]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_get_update_delete_activity(client, register_user):
    user, _token, headers = register_user()
    created = client.post(
        "/api/activities", headers=headers, json={"title": "Original", "subject": "S", "host_id": user["id"]}
    ).json()
    activity_id = created["id"]

    got = client.get(f"/api/activities/{activity_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["title"] == "Original"

    updated = client.put(
        f"/api/activities/{activity_id}", headers=headers, json={"title": "Renamed"}
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Renamed"
    assert updated.json()["subject"] == "S"  # untouched fields survive a partial update

    deleted = client.delete(f"/api/activities/{activity_id}", headers=headers)
    assert deleted.status_code == 204

    assert client.get(f"/api/activities/{activity_id}", headers=headers).status_code == 404


def test_get_unknown_activity_404s(client, register_user):
    _user, _token, headers = register_user()
    assert client.get("/api/activities/999999", headers=headers).status_code == 404


def test_attendances_list_is_empty_for_new_activity(client, register_user):
    user, _token, headers = register_user()
    activity = client.post(
        "/api/activities", headers=headers, json={"title": "T", "subject": "S", "host_id": user["id"]}
    ).json()
    resp = client.get(f"/api/activities/{activity['id']}/attendances", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_activities_endpoints_blocked_until_password_changed(client, bulk_user):
    user, _token, headers = bulk_user()
    assert client.get("/api/activities", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/activities", headers=headers, json={"title": "T", "subject": "S", "host_id": user.id}
        ).status_code
        == 403
    )
