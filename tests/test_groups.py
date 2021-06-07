# -*- coding: utf-8 -*-
"""Test the /groups endpoint"""
import pytest


def test_get_users(default_groups, client):  # pylint: disable=unused-argument
    """Test listing existing groups."""
    response = client.get("/groups")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.xfail
def test_get_single_user(default_groups, client):  # pylint: disable=unused-argument
    """Test retrieving a single group."""
    response = client.get("/groups/1")
    print(response.json())
    assert response.status_code == 200
    assert response.json()["label"] == "test_label_1"


def test_create_group(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new group."""
    response = client.post("/groups", json={"label": "test_label_create"})
    assert response.status_code == 200, response.content

    response = client.get("/groups")
    first_names = [group["label"] for group in response.json()]
    assert "test_label_create" in first_names
