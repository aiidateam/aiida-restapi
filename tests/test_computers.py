# -*- coding: utf-8 -*-
"""Test the /computers endpoint"""


def test_get_computers(default_computers, client):  # pylint: disable=unused-argument
    """Test listing existing computer."""
    response = client.get("/computers/")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_computers_projectable(client):
    """Test get projectable properites for computer."""
    response = client.get("/computers/projectable_properties")

    assert response.status_code == 200
    assert response.json() == [
        "id",
        "uuid",
        "name",
        "hostname",
        "scheduler_type",
        "transport_type",
        "metadata",
    ]


def test_get_single_computers(
    default_computers, client
):  # pylint: disable=unused-argument
    """Test retrieving a single computer."""

    for comp_id in default_computers:
        response = client.get("/computers/{}".format(comp_id))
        assert response.status_code == 200


def test_create_computer(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new computer."""
    response = client.post(
        "/computers",
        json={
            "name": "test_comp",
            "hostname": "fake_host",
            "transport_type": "local",
            "scheduler_type": "pbspro",
        },
    )
    assert response.status_code == 200, response.content

    response = client.get("/computers")
    computers = [comp["name"] for comp in response.json()]
    assert "test_comp" in computers
