# -*- coding: utf-8 -*-
"""Test the /nodes endpoint"""


def test_create_dict(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new dict."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "Dict",
            "attributes": {"x": 1, "y": 2},
            "label": "test_dict",
        },
    )
    assert response.status_code == 200, response.content


def test_create_list(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new list."""
    response = client.post(
        "/nodes",
        json={
            "node_type": "List",
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
            "node_type": "Int",
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
            "node_type": "Float",
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
            "node_type": "String",
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
            "node_type": "Bool",
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
            "node_type": "StructureData",
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
        files=None,
    )

    assert response.status_code == 200, response.content
