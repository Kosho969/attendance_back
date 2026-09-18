WORKSHOP_SURVEY_PAYLOAD = {
    "enjoyment": 5,
    "learning": 4,
    "applicability": 5,
    "second_part_wanted": True,
    "instructor_competence": 5,
    "workshop_suggestion": "Más ejemplos prácticos, por favor.",
    "instructor_suggestion": None,
}

EVENT_SURVEY_PAYLOAD = {
    "overall_rating": 5,
    "workshops_informative": 4,
    "desired_level": "intermedio",
    "would_participate_again": True,
    "interested_in_hosting": True,
    "most_enjoyed": "convivencia",
}


def _checkin(client, activity, email="jose@example.com", name="José Muñoz"):
    resp = client.post(f"/api/checkin/{activity.qr_token}", json={"name": name, "email": email})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_workshop_survey_requires_a_prior_checkin(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])

    resp = client.post(
        f"/api/checkin/{activity.qr_token}/survey",
        json={**WORKSHOP_SURVEY_PAYLOAD, "email": "never-checked-in@example.com"},
    )
    assert resp.status_code == 422
    assert "email" in resp.json()["errors"]


def test_workshop_survey_requires_checkin_to_this_specific_activity(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity_a = make_activity(host_id=user["id"], title="A")
    activity_b = make_activity(host_id=user["id"], title="B")
    _checkin(client, activity_a)  # checked into A, not B

    resp = client.post(
        f"/api/checkin/{activity_b.qr_token}/survey", json={**WORKSHOP_SURVEY_PAYLOAD, "email": "jose@example.com"}
    )
    assert resp.status_code == 422


def test_workshop_survey_submit_and_upsert(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])
    _checkin(client, activity)

    first = client.post(
        f"/api/checkin/{activity.qr_token}/survey", json={**WORKSHOP_SURVEY_PAYLOAD, "email": "jose@example.com"}
    )
    assert first.status_code == 201
    body = first.json()
    assert body["enjoyment"] == 5
    assert body["workshop_suggestion"] == "Más ejemplos prácticos, por favor."
    assert body["attendee"]["email"] == "jose@example.com"

    updated_payload = {**WORKSHOP_SURVEY_PAYLOAD, "email": "jose@example.com", "enjoyment": 2}
    second = client.post(f"/api/checkin/{activity.qr_token}/survey", json=updated_payload)
    assert second.status_code == 201
    assert second.json()["id"] == body["id"]  # same row, updated in place
    assert second.json()["enjoyment"] == 2


def test_workshop_survey_rejects_out_of_range_rating(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])
    _checkin(client, activity)

    resp = client.post(
        f"/api/checkin/{activity.qr_token}/survey",
        json={**WORKSHOP_SURVEY_PAYLOAD, "email": "jose@example.com", "enjoyment": 6},
    )
    assert resp.status_code == 422
    assert "enjoyment" in resp.json()["errors"]


def test_event_survey_requires_an_existing_attendee(client):
    resp = client.post("/api/event-survey", json={**EVENT_SURVEY_PAYLOAD, "email": "nobody@example.com"})
    assert resp.status_code == 422
    assert "email" in resp.json()["errors"]


def test_event_survey_submit_and_upsert(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])
    _checkin(client, activity)

    first = client.post("/api/event-survey", json={**EVENT_SURVEY_PAYLOAD, "email": "jose@example.com"})
    assert first.status_code == 201
    assert first.json()["desired_level"] == "intermedio"

    updated = client.post(
        "/api/event-survey",
        json={**EVENT_SURVEY_PAYLOAD, "email": "jose@example.com", "desired_level": "alto"},
    )
    assert updated.status_code == 201
    assert updated.json()["id"] == first.json()["id"]
    assert updated.json()["desired_level"] == "alto"


def test_event_survey_rejects_invalid_enum_value(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity = make_activity(host_id=user["id"])
    _checkin(client, activity)

    resp = client.post(
        "/api/event-survey",
        json={**EVENT_SURVEY_PAYLOAD, "email": "jose@example.com", "desired_level": "extremo"},
    )
    assert resp.status_code == 422


def test_checkin_response_reflects_event_survey_completion(client, register_user, make_activity):
    user, _token, _headers = register_user()
    activity_a = make_activity(host_id=user["id"], title="A")
    activity_b = make_activity(host_id=user["id"], title="B")

    first_checkin = _checkin(client, activity_a)
    assert first_checkin["event_survey_completed"] is False

    client.post("/api/event-survey", json={**EVENT_SURVEY_PAYLOAD, "email": "jose@example.com"})

    second_checkin = _checkin(client, activity_b)
    assert second_checkin["event_survey_completed"] is True


def test_survey_listing_endpoints_require_auth(client):
    assert client.get("/api/activities/1/surveys").status_code == 401
    assert client.get("/api/event-surveys").status_code == 401


def test_survey_listing_endpoints_return_submitted_responses(client, register_user, make_activity):
    user, _token, headers = register_user()
    activity = make_activity(host_id=user["id"])
    _checkin(client, activity)
    client.post(
        f"/api/checkin/{activity.qr_token}/survey", json={**WORKSHOP_SURVEY_PAYLOAD, "email": "jose@example.com"}
    )
    client.post("/api/event-survey", json={**EVENT_SURVEY_PAYLOAD, "email": "jose@example.com"})

    workshop_surveys = client.get(f"/api/activities/{activity.id}/surveys", headers=headers)
    assert workshop_surveys.status_code == 200
    assert len(workshop_surveys.json()) == 1
    assert workshop_surveys.json()[0]["attendee"]["email"] == "jose@example.com"

    event_surveys = client.get("/api/event-surveys", headers=headers)
    assert event_surveys.status_code == 200
    assert len(event_surveys.json()) == 1
