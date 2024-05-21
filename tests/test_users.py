# -*- coding: utf-8 -*-
"""Test the /users endpoint"""


def test_get_single_user(default_users, client):  # pylint: disable=unused-argument
    """Test retrieving a single user."""
    for user_id in default_users:
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200


def test_get_users(default_users, client):  # pylint: disable=unused-argument
    """Test listing existing users.

    Note: Besides the default users set up by the pytest fixture the test profile
    includes a default user.
    """
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2 + 1


def test_create_user(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new user."""
    response = client.post(
        "/users", json={"first_name": "New", "email": "aiida@localhost"}
    )
    assert response.status_code == 200, response.content

    response = client.get("/users")
    first_names = [user["first_name"] for user in response.json()]
    assert "New" in first_names


def test_get_users_projectable(client):
    """Test get projectable properites for users."""
    response = client.get("/users/projectable_properties")

    assert response.status_code == 200
    assert response.json() == ["id", "email", "first_name", "last_name", "institution"]
