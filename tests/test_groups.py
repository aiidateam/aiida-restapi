# -*- coding: utf-8 -*-
"""Test the /groups endpoint"""


def test_get_group(default_groups, client):  # pylint: disable=unused-argument
    """Test listing existing groups."""
    response = client.get("/groups")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_group_projectable(client):
    """Test get projectable properites for group."""
    response = client.get("/groups/projectable_properties")

    assert response.status_code == 200
    assert response.json() == [
        "id",
        "uuid",
        "label",
        "type_string",
        "description",
        "extras",
        "time",
        "user_id",
    ]


def test_get_single_group(default_groups, client):  # pylint: disable=unused-argument
    """Test retrieving a single group."""

    for group_id in default_groups:
        response = client.get(f"/groups/{group_id}")
        assert response.status_code == 200


def test_create_group(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new group."""
    response = client.post("/groups", json={"label": "test_label_create"})
    assert response.status_code == 200, response.content

    response = client.get("/groups")
    first_names = [group["label"] for group in response.json()]

    assert "test_label_create" in first_names


def test_create_group_returns_user_id(
    client, authenticate
):  # pylint: disable=unused-argument
    """Test creating a new group returns user_id."""
    response = client.post("/groups", json={"label": "test_label_create"})
    assert response.status_code == 200, response.content

    assert response.json()["user_id"]
