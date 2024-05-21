# -*- coding: utf-8 -*-
"""Test the /nodes endpoint"""


import io


def test_get_nodes_projectable(client):
    """Test get projectable properites for nodes."""
    response = client.get("/nodes/projectable_properties")

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


def test_get_single_nodes(default_nodes, client):  # pylint: disable=unused-argument
    """Test retrieving a single nodes."""

    for nodes_id in default_nodes:
        response = client.get(f"/nodes/{nodes_id}")
        assert response.status_code == 200


def test_get_nodes(default_nodes, client):  # pylint: disable=unused-argument
    """Test listing existing nodes."""
    response = client.get("/nodes")
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_create_dict(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new dict."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.dict",
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
                "entry_point": "core.code.installed",
                "dbcomputer_id": comp_id,
                "attributes": {"filepath_executable": "/bin/true"},
                "label": "test_code",
            },
        )
    assert response.status_code == 200, response.content


def test_create_list(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new list."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.list",
            "attributes": {"list": [2, 3]},
        },
    )

    assert response.status_code == 200, response.content


def test_create_int(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Int."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.int",
            "attributes": {"value": 6},
        },
    )
    assert response.status_code == 200, response.content


def test_create_float(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Float."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.float",
            "attributes": {"value": 6.6},
        },
    )
    assert response.status_code == 200, response.content


def test_create_string(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new string."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.str",
            "attributes": {"value": "test_string"},
        },
    )
    assert response.status_code == 200, response.content


def test_create_bool(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Bool."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.bool",
            "attributes": {"value": "True"},
        },
    )
    assert response.status_code == 200, response.content


def test_create_structure_data(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new StructureData."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.structure",
            "process_type": None,
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
            "entry_point": "core.orbital",
            "process_type": None,
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
        "entry_point": "core.singlefile",
        "process_type": None,
        "description": "Testing single upload file",
        "attributes": {},
    }

    response = client.post("/nodes/singlefile", files=test_file, data=params)

    assert response.status_code == 200


def test_create_node_wrong_value(
    client, authenticate
):  # pylint: disable=unused-argument
    """Test creating a new node with wrong value."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.float",
            "attributes": {"value": "tests"},
        },
    )
    assert response.status_code == 400, response.content

    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.int",
            "attributes": {"value": "tests"},
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
            "entry_point": "core.str",
            "attributes": {"value1": 5},
        },
    )
    assert response.status_code == 400, response.content


def test_create_unknown_entry_point(
    default_computers, client, authenticate
):  # pylint: disable=unused-argument
    """Test error message when specifying unknown ``entry_point``."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.not.existing.entry.point",
            "label": "test_code",
        },
    )
    assert response.status_code == 404, response.content
    assert (
        response.json()["detail"]
        == "Entry point 'core.not.existing.entry.point' not found in group 'aiida.data'"
    )


def test_create_additional_attribute(
    default_computers, client, authenticate
):  # pylint: disable=unused-argument
    """Test adding additional properties returns errors."""

    for comp_id in default_computers:
        response = client.post(
            "/nodes",
            json={
                "uuid": "3",
                "entry_point": "core.code.installed",
                "dbcomputer_id": comp_id,
                "attributes": {"filepath_executable": "/bin/true"},
                "label": "test_code",
            },
        )
    assert response.status_code == 422, response.content


def test_create_bool_with_extra(
    client, authenticate
):  # pylint: disable=unused-argument
    """Test creating a new Bool with extra."""
    response = client.post(
        "/nodes",
        json={
            "entry_point": "core.bool",
            "attributes": {"value": "True"},
            "extras": {"extra_one": "value_1", "extra_two": "value_2"},
        },
    )

    check_response = client.get(f"/nodes/{response.json()['id']}")

    assert check_response.status_code == 200, response.content
    assert check_response.json()["extras"]["extra_one"] == "value_1"
    assert check_response.json()["extras"]["extra_two"] == "value_2"
