# -*- coding: utf-8 -*-
"""Test the /computers endpoint"""


def test_get_computers(default_computers, client):  # pylint: disable=unused-argument
    """Test listing existing computer."""
    response = client.get("/computers/")
    # print(response)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_single_computers(
    default_computers, client
):  # pylint: disable=unused-argument
    """Test listing existing computers."""
    response = client.get("/computers/1")
    assert response.status_code == 200


def test_create_computer(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new computer."""
    response = client.post(
        "/computers",
        json={
            "label": "test_comp",
            "hostname": "fake_host",
            "transport_type": "local",
            "scheduler_type": "pbspro",
        },
    )
    assert response.status_code == 200, response.content

    response = client.get("/computers")
    computers = [comp["test_comp"] for comp in response.json()]
    assert "test_comp" in computers
