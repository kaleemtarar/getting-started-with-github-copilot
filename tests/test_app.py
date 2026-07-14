import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture
def client():
    app_module.activities = copy.deepcopy(ORIGINAL_ACTIVITIES)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities_returns_catalog(client):
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unregister_participant_removes_existing_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"

    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]


def test_unregister_unknown_participant_returns_404(client):
    # Arrange
    activity_name = "Chess Club"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
