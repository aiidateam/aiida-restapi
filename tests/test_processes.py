# -*- coding: utf-8 -*-
"""Test the /processes endpoint"""


def test_get_processes(example_processes, client):  # pylint: disable=unused-argument
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
    example_processes, client
):  # pylint: disable=unused-argument
    """Test retrieving a single processes."""
    for proc_id in example_processes:
        response = client.get("/processes/{}".format(proc_id))
        assert response.status_code == 200


def test_add_process(
    default_test_add_process, client, authenticate
):  # pylint: disable=unused-argument
    """Test adding new process"""
    code_id, x_id, y_id = default_test_add_process
    response = client.post(
        "/processes",
        json={
            "label": "test_new_process",
            "process_entry_point": "arithmetic.add",
            "inputs": {
                "code.id": code_id,
                "x.id": x_id,
                "y.id": y_id,
                "metadata": {
                    "description": "Test job submission with the add plugin",
                },
            },
        },
    )
    assert response.status_code == 200
