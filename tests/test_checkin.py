def test_show_activity_by_unknown_token_404s(client):
    assert client.get("/api/checkin/not-a-real-token").status_code == 404


def test_show_activity_is_public_and_does_not_need_auth(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])

    resp = client.get(f"/api/checkin/{activity.qr_token}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == activity.title
    assert body["host"]["id"] == user["id"]


def test_checkin_creates_attendee_and_attendance(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])

    resp = client.post(
        f"/api/checkin/{activity.qr_token}", json={"name": "José Muñoz", "email": "jose@example.com"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["attendee"]["name"] == "José Muñoz"
    assert body["already_checked_in"] is False
    assert body["event_survey_completed"] is False


def test_checkin_twice_is_idempotent_and_reports_already_checked_in(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])

    first = client.post(
        f"/api/checkin/{activity.qr_token}", json={"name": "Jose", "email": "jose@example.com"}
    ).json()
    second = client.post(
        f"/api/checkin/{activity.qr_token}", json={"name": "Jose", "email": "jose@example.com"}
    ).json()

    assert first["already_checked_in"] is False
    assert second["already_checked_in"] is True
    assert first["attendee"]["id"] == second["attendee"]["id"]
    assert first["checked_in_at"] == second["checked_in_at"]  # timestamp isn't bumped on repeat check-in


def test_checkin_rejects_invalid_email(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])

    resp = client.post(f"/api/checkin/{activity.qr_token}", json={"name": "Jose", "email": "not-an-email"})
    assert resp.status_code == 422


def test_checkin_to_unknown_token_404s(client):
    resp = client.post("/api/checkin/does-not-exist", json={"name": "Jose", "email": "jose@example.com"})
    assert resp.status_code == 404


def test_same_attendee_can_check_into_multiple_activities(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity_a = make_activity(host_id=user["id"], title="A")
    activity_b = make_activity(host_id=user["id"], title="B")

    resp_a = client.post(
        f"/api/checkin/{activity_a.qr_token}", json={"name": "Jose", "email": "jose@example.com"}
    ).json()
    resp_b = client.post(
        f"/api/checkin/{activity_b.qr_token}", json={"name": "Jose", "email": "jose@example.com"}
    ).json()

    # Same person, same Attendee row, reused across activities.
    assert resp_a["attendee"]["id"] == resp_b["attendee"]["id"]
