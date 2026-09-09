def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_index_is_available(client):
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "Mergington High School Activities" in response.text


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert "Basketball Team" in activities
    assert set(activities["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }
    assert "michael@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_adds_student_to_activity(client):
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Basketball Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Basketball Team"
    }
    activities = client.get("/activities").json()
    assert email in activities["Basketball Team"]["participants"]


def test_duplicate_signup_is_rejected_without_adding_participant(client):
    email = "michael@mergington.edu"
    original_participants = client.get("/activities").json()["Chess Club"][
        "participants"
    ]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == original_participants
    assert participants.count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client):
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_unregister_removes_student_from_activity(client):
    email = "remove.student@mergington.edu"
    client.post("/activities/Swimming Club/signup", params={"email": email})

    response = client.delete(
        "/activities/Swimming Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Swimming Club"
    }
    activities = client.get("/activities").json()
    assert email not in activities["Swimming Club"]["participants"]


def test_unregister_rejects_nonparticipant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_requires_email(client):
    response = client.delete("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_signup_then_unregister_returns_activity_to_original_state(client):
    email = "cycle.student@mergington.edu"
    initial_participants = client.get("/activities").json()["Art Studio"][
        "participants"
    ]

    signup_response = client.post(
        "/activities/Art Studio/signup",
        params={"email": email},
    )
    unregister_response = client.delete(
        "/activities/Art Studio/signup",
        params={"email": email},
    )

    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    participants = client.get("/activities").json()["Art Studio"]["participants"]
    assert participants == initial_participants
