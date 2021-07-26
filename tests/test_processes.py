# -*- coding: utf-8 -*-
"""Test the /processes endpoint"""


def test_get_processes(default_process, client):  # pylint: disable=unused-argument
    """Test listing existing processes."""
    response = client.get("/processes/")

    assert response.status_code == 200
    assert len(response.json()) == 12


def test_get_processes_projectable(client):
    """Test get projectable properites for processes."""
    response = client.get("/processes/projectable_properties")

    assert response.status_code == 200
    assert response.json() == [
        "id",
        "uuid",
        "node_type",
        "process_type",
        "label",
        "description",
        "ctime",
        "mtime",
        "user_id",
        "dbcomputer_id",
        "attributes",
        "extras",
    ]


def test_get_single_processes(
    default_process, client
):  # pylint: disable=unused-argument
    """Test retrieving a single processes."""
    for proc_id in default_process:
        response = client.get("/processes/{}".format(proc_id))
        assert response.status_code == 200
