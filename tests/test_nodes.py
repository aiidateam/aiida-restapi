# -*- coding: utf-8 -*-
"""Test the /nodes endpoint"""


import io


def test_create_dict(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new dict."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.dict.Dict.|",
            "attributes": {"x": 1, "y": 2},
            "label": "test_dict",
        },
    )
    assert response.status_code == 200, response.content


def test_create_code(
    default_computers, client, authenticate
):  # pylint: disable=unused-argument
    """Test creating a new Code."""

    for comp_id in default_computers:
        response = client.post(
            "/nodes",
            json={
                "node_type": "data.code.Code.|",
                "dbcomputer_id": comp_id,
                "attributes": {"is_local": False, "remote_exec_path": "/bin/true"},
                "label": "test_code",
            },
        )
    assert response.status_code == 200, response.content


def test_create_list(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new list."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.list.List.|",
            "attributes": {"list": [2, 3]},
            "label": "test_list",
        },
    )

    assert response.status_code == 200, response.content


def test_create_int(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Int."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.int.Int.|",
            "attributes": {"value": 6},
            "label": "test_Int",
        },
    )
    assert response.status_code == 200, response.content


def test_create_float(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Float."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.float.Float.|",
            "attributes": {"value": 6.6},
            "label": "test_Float",
        },
    )
    assert response.status_code == 200, response.content


def test_create_string(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new string."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.str.Str.|",
            "attributes": {"value": "test_string"},
            "label": "test_string",
        },
    )
    assert response.status_code == 200, response.content


def test_create_bool(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Bool."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.bool.Bool.|",
            "attributes": {"value": "True"},
            "label": "test_bool",
        },
    )
    assert response.status_code == 200, response.content


def test_create_structure_data(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new StructureData."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.structure.StructureData.|",
            "process_type": None,
            "label": "test_StructureData",
            "description": "",
            "attributes": {
                "cell": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                "pbc": [True, True, True],
                "ase": None,
                "pymatgen": None,
                "pymatgen_structure": None,
                "pymatgen_molecule": None,
            },
        },
    )

    assert response.status_code == 200, response.content


def test_create_orbital_data(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new OrbitalData."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.orbital.OrbitalData.|",
            "process_type": None,
            "label": "test_OrbitalData",
            "description": "",
            "attributes": {
                "orbital_dicts": [
                    {
                        "spin": 0,
                        "position": [
                            -1,
                            1,
                            1,
                        ],
                        "kind_name": "As",
                        "diffusivity": None,
                        "radial_nodes": 0,
                        "_orbital_type": "realhydrogen",
                        "x_orientation": None,
                        "z_orientation": None,
                        "angular_momentum": -3,
                    }
                ]
            },
        },
    )

    assert response.status_code == 200, response.content


def test_create_single_file_upload(
    client, authenticate
):  # pylint: disable=unused-argument
    """Testing file upload"""
    test_file = {
        "upload_file": (
            "test_file.txt",
            io.BytesIO(b"Some test strings"),
            "multipart/form-data",
        )
    }
    params = {
        "node_type": "data.singlefile.SingleFileData.|",
        "process_type": None,
        "label": "test_upload_file",
        "description": "Testing single upload file",
        "attributes": {},
    }

    response = client.post("/singlefiledata", files=test_file, data=params)

    assert response.status_code == 200


def test_create_node_wrond_value(
    client, authenticate
):  # pylint: disable=unused-argument
    """Test creating a new node with wrong value."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.float.Float.|",
            "attributes": {"value": "tests"},
            "label": "test_Float",
        },
    )
    assert response.status_code == 400, response.content

    response = client.post(
        "/nodes",
        json={
            "node_type": "data.int.Int.|",
            "attributes": {"value": "tests"},
            "label": "test_int",
        },
    )
    assert response.status_code == 400, response.content


def test_create_node_wrong_attribute(
    client, authenticate
):  # pylint: disable=unused-argument
    """Test adding node with wrong attributes."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.str.Str.|",
            "attributes": {"value1": 5},
            "label": "test_int",
        },
    )
    assert response.status_code == 400, response.content


def test_wrong_entry_point(client, authenticate):  # pylint: disable=unused-argument
    """Test adding node with wrong entry point."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "data.float.wrong.|",
            "attributes": {"value": 3},
            "label": "test_Float",
        },
    )
    assert response.status_code == 404, response.content
