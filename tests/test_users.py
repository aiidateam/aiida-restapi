# -*- coding: utf-8 -*-
"""Test the /users endpoint"""
import pytest


@pytest.mark.xfail
def test_get_single_user(default_users, client):  # pylint: disable=unused-argument
    """Test retrieving a single user."""
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["first_name"] == "Giuseppe"


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
