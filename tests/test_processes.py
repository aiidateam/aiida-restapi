# -*- coding: utf-8 -*-
"""Test the /processes endpoint"""
import io

from aiida.orm import Dict, SinglefileData


def test_get_processes(example_processes, client):  # pylint: disable=unused-argument
    """Test listing existing processes."""
    response = client.get("/processes/")

    assert response.status_code == 200
    assert len(response.json()) == 12


def test_get_processes_projectable(client):
    """Test get projectable properties for processes."""
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
        "repository_metadata",
    ]


def test_get_single_processes(
    example_processes, client
):  # pylint: disable=unused-argument
    """Test retrieving a single processes."""
    for proc_id in example_processes:
        response = client.get(f"/processes/{proc_id}")
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
            "process_entry_point": "aiida.calculations:core.arithmetic.add",
            "inputs": {
                "code.uuid": code_id,
                "x.uuid": x_id,
                "y.uuid": y_id,
                "metadata": {
                    "description": "Test job submission with the add plugin",
                },
            },
        },
    )
    assert response.status_code == 200


def test_add_process_invalid_entry_point(
    default_test_add_process, client, authenticate
):  # pylint: disable=unused-argument
    """Test adding new process with invalid entry point"""
    code_id, x_id, y_id = default_test_add_process
    response = client.post(
        "/processes",
        json={
            "label": "test_new_process",
            "process_entry_point": "wrong_entry_point",
            "inputs": {
                "code.uuid": code_id,
                "x.uuid": x_id,
                "y.uuid": y_id,
                "metadata": {
                    "description": "Test job submission with the add plugin",
                },
            },
        },
    )
    assert response.status_code == 404


def test_add_process_invalid_node_id(
    default_test_add_process, client, authenticate
):  # pylint: disable=unused-argument
    """Test adding new process with invalid Node ID"""
    code_id, x_id, _ = default_test_add_process
    response = client.post(
        "/processes",
        json={
            "label": "test_new_process",
            "process_entry_point": "aiida.calculations:core.arithmetic.add",
            "inputs": {
                "code.uuid": code_id,
                "x.uuid": x_id,
                "y.uuid": "891a9efa-f90e-11eb-9a03-0242ac130003",
                "metadata": {
                    "description": "Test job submission with the add plugin",
                },
            },
        },
    )
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Node with UUID `891a9efa-f90e-11eb-9a03-0242ac130003` does not exist."
    }


def test_add_process_nested_inputs(
    default_test_add_process, client, authenticate
):  # pylint: disable=unused-argument
    """Test adding new process that has nested inputs"""
    code_id, _, _ = default_test_add_process
    template = Dict(
        {
            "files_to_copy": [("file", "file.txt")],
        }
    ).store()
    single_file = SinglefileData(io.StringIO("content")).store()

    response = client.post(
        "/processes",
        json={
            "label": "test_new_process",
            "process_entry_point": "aiida.calculations:core.templatereplacer",
            "inputs": {
                "code.uuid": code_id,
                "template.uuid": template.uuid,
                "files": {"file.uuid": single_file.uuid},
                "metadata": {
                    "description": "Test job submission with the add plugin",
                    "options": {
                        "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1}
                    },
                },
            },
        },
    )
    assert response.status_code == 200
