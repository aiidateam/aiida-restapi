"""Test the /nodes endpoint"""

from __future__ import annotations

import io
import json
import typing as t

import pytest
from aiida import orm
from fastapi.testclient import TestClient
from httpx import AsyncClient

if t.TYPE_CHECKING:
    from pydantic import BaseModel


def test_get_node_schema(client: TestClient):
    """Test get schema for nodes."""
    response = client.get('/nodes/schema')
    assert response.status_code == 200
    result = response.json()
    assert 'properties' in result
    assert sorted(result['properties'].keys()) == sorted(orm.Node.fields.keys())
    assert 'attributes' in result['properties']
    attributes = result['properties']['attributes']
    assert '$ref' in attributes
    assert attributes['$ref'].endswith('AttributesModel')
    assert '$defs' in result
    assert 'AttributesModel' in result['$defs']
    assert not result['$defs']['AttributesModel']['properties']


@pytest.mark.parametrize(
    'which, model, name',
    [
        ['get', orm.Int.Model, 'AttributesModel'],
        ['post', orm.Int.CreateModel, 'AttributesCreateModel'],
    ],
)
def test_get_node_schema_by_type(client: TestClient, which: str, model: type[BaseModel], name: str):
    """Test get schema for nodes by valid type."""
    response = client.get(f'/nodes/schema?type=data.core.int.Int.&which={which}')
    assert response.status_code == 200
    result = response.json()
    assert 'properties' in result
    assert sorted(result['properties'].keys()) == sorted(model.model_fields.keys())
    assert 'attributes' in result['properties']
    attributes = result['properties']['attributes']
    assert '$ref' in attributes
    assert attributes['$ref'].endswith(name)
    assert '$defs' in result
    assert name in result['$defs']
    assert result['$defs'][name]['title'] == f'Int{name}'
    assert result['$defs'][name]['properties']
    fields = orm.Int.fields.keys()
    assert all(f'attributes.{key}' in fields for key in result['$defs'][name]['properties'].keys())


def test_get_node_schema_by_invalid_type(client: TestClient):
    """Test get schema for nodes with invalid type."""
    response = client.get('/nodes/schema?type=this_is_not_a_valid_type')
    assert response.status_code == 422


def test_get_node_projections(client: TestClient):
    """Test get projections for nodes."""
    response = client.get('/nodes/projections')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Node.fields.keys())


def test_get_node_projections_by_type(client: TestClient):
    """Test get projections for nodes by valid type."""
    response = client.get('/nodes/projections?type=data.core.int.Int.')
    assert response.status_code == 200
    result = response.json()
    assert result == sorted(orm.Int.fields.keys())
    assert 'attributes.source' in result
    assert 'attributes.value' in result


def test_get_node_projections_by_invalid_type(client: TestClient):
    """Test get projections for nodes with invalid type."""
    response = client.get('/nodes/projections?type=this_is_not_a_valid_type')
    assert response.status_code == 422


def test_get_nodes_statistics(client: TestClient):
    """Test get statistics for nodes."""
    from aiida_restapi.models.node import NodeStatistics

    response = client.get('/nodes/statistics')
    assert response.status_code == 200
    result = response.json()
    assert NodeStatistics.model_validate(result)


def test_get_download_formats(client: TestClient):
    """Test get download formats for nodes."""
    response = client.get('/nodes/download_formats')

    assert response.status_code == 200

    reference = {
        'data.core.array.ArrayData.|': ['json'],
        'data.core.array.bands.BandsData.|': [
            'agr',
            'agr_batch',
            'dat_blocks',
            'dat_multicolumn',
            'gnuplot',
            'json',
            'mpl_pdf',
            'mpl_png',
            'mpl_singlefile',
            'mpl_withjson',
        ],
        'data.core.array.kpoints.KpointsData.|': ['json'],
        'data.core.array.projection.ProjectionData.|': ['json'],
        'data.core.array.trajectory.TrajectoryData.|': ['cif', 'json', 'xsf'],
        'data.core.array.xy.XyData.|': ['json'],
        'data.core.cif.CifData.|': ['cif'],
        'data.core.structure.StructureData.|': ['chemdoodle', 'cif', 'xsf', 'xyz'],
        'data.core.upf.UpfData.|': ['json', 'upf'],
    }
    response_json = response.json()

    for key, value in reference.items():
        if key not in response_json:
            raise AssertionError(f'The key {key!r} is not found in the response: {response_json}')
        if not set(value) <= set(response_json[key]):
            raise AssertionError(f'The value {value} in key {key!r} is not contained in the response: {response_json}')


@pytest.mark.usefixtures('default_nodes')
def test_get_nodes(client: TestClient):
    """Test listing existing nodes."""
    response = client.get('/nodes')
    assert response.status_code == 200
    assert len(response.json()['data']) == 4
    result = next(iter(response.json()['data']), None)
    assert result is not None
    assert set(result.keys()) == {'pk', 'uuid', 'node_type', 'label', 'description', 'ctime', 'mtime', 'user'}


@pytest.mark.usefixtures('default_nodes')
def test_get_nodes_by_type(client: TestClient):
    """Test listing existing nodes by type."""
    filters = {'node_type': {'in': ['data.core.int.Int.', 'data.core.float.Float.']}}
    response = client.get(f'/nodes?filters={json.dumps(filters)}')
    assert response.status_code == 200
    results = response.json()['data']
    assert len(results) == 2
    assert any(result['node_type'] == 'data.core.int.Int.' for result in results)
    assert any(result['node_type'] == 'data.core.float.Float.' for result in results)


@pytest.mark.usefixtures('default_nodes')
def test_get_nodes_with_filters(client: TestClient):
    """Test listing existing nodes with filters."""
    filters = {'attributes.value': 1.1}
    response = client.get(f'/nodes?filters={json.dumps(filters)}')
    assert response.status_code == 200
    results = response.json()['data']
    assert len(results) == 1
    assert results[0]['node_type'] == 'data.core.float.Float.'

    # Attributes are excluded, so we need to check separately by id
    check = client.get(f'/nodes/{results[0]["uuid"]}/attributes')
    assert check.status_code == 200
    assert check.json()['value'] == 1.1


@pytest.mark.usefixtures('default_nodes')
def test_get_nodes_in_order(client: TestClient):
    """Test listing existing nodes in order."""
    order_by = {'ctime': 'desc'}
    response = client.get(f'/nodes?order_by={json.dumps(order_by)}')
    assert response.status_code == 200
    results = response.json()['data']
    assert len(results) == 4
    ctimes = [result['ctime'] for result in results]
    assert ctimes == sorted(ctimes, reverse=True)


@pytest.mark.usefixtures('default_nodes')
def test_get_nodes_pagination(client: TestClient):
    """Test listing existing nodes with pagination."""
    response = client.get('/nodes?page_size=2&page=1')
    assert response.status_code == 200
    results = response.json()['data']
    assert len(results) == 2
    assert all(result['pk'] in (1, 2) for result in results)

    response = client.get('/nodes?page_size=2&page=2')
    assert response.status_code == 200
    results = response.json()['data']
    assert len(results) == 2
    assert all(result['pk'] in (3, 4) for result in results)


def test_get_node_types(client: TestClient):
    """Test retrieving the available node types."""
    from aiida.plugins import get_entry_points

    from aiida_restapi.models.node import NodeType

    response = client.get('/nodes/types')
    assert response.status_code == 200
    result = response.json()
    entry_points = get_entry_points('aiida.data') + get_entry_points('aiida.node')
    assert len(result) == len(entry_points)
    first = result[0]
    assert NodeType.model_validate(first)


def test_get_node(client: TestClient, default_nodes: list[str | None]):
    """Test retrieving a single nodes."""
    for node_id in default_nodes:
        response = client.get(f'/nodes/{node_id}')
        assert response.status_code == 200, response.content
        assert response.json()['uuid'] == node_id


def test_get_node_user(client: TestClient):
    """Test retrieving the user of a single node."""
    node = orm.Int(value=5).store()
    response = client.get(f'/nodes/{node.uuid}/user')
    assert response.status_code == 200
    data = response.json()
    assert data['email'] == node.user.email


def test_get_node_computer(client: TestClient, default_computers: list[int | None]):
    """Test retrieving the computer of a single node."""
    computer = orm.load_computer(default_computers[0])
    node = orm.Int(value=5, computer=computer).store()
    response = client.get(f'/nodes/{node.uuid}/computer')
    assert response.status_code == 200
    data = response.json()
    assert data['pk'] == node.computer.pk


def test_get_node_no_computer(client: TestClient):
    """Test retrieving the computer of a node with null computer raises an exception."""
    node = orm.Int(value=5).store()
    response = client.get(f'/nodes/{node.uuid}/computer')
    assert response.status_code == 404
    assert response.json()['detail'] == f'Computer related to Node<{node.uuid}> not found.'


def test_get_node_groups(client: TestClient, default_groups: list[str]):
    """Test retrieving groups of a single node."""
    node = orm.Int(value=10).store()
    for group_id in default_groups:
        group = orm.load_group(group_id)
        group.add_nodes([node])
    response = client.get(f'/nodes/{node.uuid}/groups')
    assert response.status_code == 200
    data = response.json()['data']
    returned_group_ids = {item['uuid'] for item in data}
    assert returned_group_ids == set(default_groups)


def test_get_node_attributes(client: TestClient, default_nodes: list[str | None]):
    """Test retrieving attributes of a single node."""
    for node_id in default_nodes:
        response = client.get(f'/nodes/{node_id}/attributes')
        assert response.status_code == 200
        data = response.json()
        node = orm.load_node(node_id)
        for key, value in node.base.attributes.items():
            assert key in data
            assert data[key] == value


def test_get_node_extras(client: TestClient, default_nodes: list[str | None]):
    """Test retrieving extras of a single node."""
    for node_id in default_nodes:
        response = client.get(f'/nodes/{node_id}/extras')
        assert response.status_code == 200
        data = response.json()
        node = orm.load_node(node_id)
        for key, value in node.base.extras.items():
            assert key in data
            assert data[key] == value


def test_get_node_links(client: TestClient, mock_arithmetic_add: str):
    """Test retrieving links of a single node."""

    calc = orm.load_node(mock_arithmetic_add)

    response = client.get(f'/nodes/{calc.uuid}/links?direction=incoming')
    assert response.status_code == 200
    assert len(response.json()['data']) == 2  # x and y

    response = client.get(f'/nodes/{calc.uuid}/links?direction=outgoing')
    assert response.status_code == 200
    assert len(response.json()['data']) == 1  # sum


def test_get_node_repository_metadata(client: TestClient, array_data_node: orm.ArrayData):
    """Test retrieving repository metadata for a node."""
    response = client.get(f'/nodes/{array_data_node.uuid}/repo/metadata')
    assert response.status_code == 200
    result = response.json()
    default = orm.ArrayData.default_array_name + '.npy'
    assert default in result
    assert all(t in result[default] for t in ('type', 'binary', 'size', 'download'))
    assert result[default]['type'] == 'FILE'
    assert result[default]['binary'] is True
    assert 'zipped' in result
    assert all(t in result['zipped'] for t in ('type', 'binary', 'size', 'download'))
    assert result['zipped']['type'] == 'FILE'
    assert result['zipped']['binary'] is True


def test_get_node_file_contents(client: TestClient, array_data_node: orm.ArrayData):
    """Test retrieving file contents for a node."""
    import numpy as np

    default = orm.ArrayData.default_array_name
    response = client.get(f'/nodes/{array_data_node.uuid}/repo/contents?filename={default}.npy')
    assert response.status_code == 200
    assert isinstance(response.content, bytes)
    array = np.load(io.BytesIO(response.content))
    assert np.array_equal(array, array_data_node.get_array(default))


@pytest.mark.usefixtures('authenticate')
def test_create_dict(client: TestClient):
    """Test creating a new dict."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.dict.Dict.',
            'label': 'test_dict',
            'attributes': {'value': {'x': 1, 'y': 2}},
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.anyio
@pytest.mark.usefixtures('authenticate')
async def test_create_code(async_client: AsyncClient, default_computers: list[int | None]):
    """Test creating a new Code."""
    for comp_id in default_computers:
        computer = orm.load_computer(comp_id)
        response = await async_client.post(
            '/nodes',
            json={
                'node_type': 'data.core.code.installed.InstalledCode.',
                'label': 'test_code',
                'attributes': {
                    'filepath_executable': '/bin/true',
                    'computer': computer.label,
                },
            },
        )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_list(client: TestClient):
    """Test creating a new list."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.list.List.',
            'attributes': {'value': [2, 3]},
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_int(client: TestClient):
    """Test creating a new Int."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.int.Int.',
            'attributes': {'value': 6},
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_float(client: TestClient):
    """Test creating a new Float."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.float.Float.',
            'attributes': {'value': 6.6},
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_string(client: TestClient):
    """Test creating a new string."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.str.Str.',
            'attributes': {'value': 'test_string'},
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_bool(client: TestClient):
    """Test creating a new Bool."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.bool.Bool.',
            'attributes': {'value': True},
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_structure_data(client: TestClient):
    """Test creating a new StructureData."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.structure.StructureData.',
            'description': '',
            'attributes': {
                'cell': [
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                ],
                'pbc1': True,
                'pbc2': True,
                'pbc3': True,
                'kinds': [
                    {
                        'name': 'H',
                        'mass': 1.00784,
                        'symbols': ['H'],
                        'weights': [1.0],
                    }
                ],
                'sites': [
                    {
                        'position': [0.0, 0.0, 0.0],
                        'kind_name': 'H',
                    },
                    {
                        'position': [0.5, 0.5, 0.5],
                        'kind_name': 'H',
                    },
                ],
            },
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_orbital_data(client: TestClient):
    """Test creating a new OrbitalData."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.orbital.OrbitalData.',
            'description': '',
            'attributes': {
                'orbital_dicts': [
                    {
                        'spin': 0,
                        'position': [
                            -1,
                            1,
                            1,
                        ],
                        'kind_name': 'As',
                        'diffusivity': None,
                        'radial_nodes': 0,
                        '_orbital_type': 'realhydrogen',
                        'x_orientation': None,
                        'z_orientation': None,
                        'angular_momentum': -3,
                    }
                ]
            },
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.usefixtures('authenticate')
def test_create_single_file(client: TestClient):
    """Testing file upload"""
    files = [
        (
            'files',
            (
                'test_file.txt',
                io.BytesIO(b'Some test strings'),
                'text/plain',
            ),
        )
    ]
    data = {
        'params': json.dumps(
            {
                'node_type': 'data.core.singlefile.SinglefileData.',
            }
        )
    }

    response = client.post('/nodes/file-upload', files=files, data=data)
    assert response.status_code == 200, response.json()

    check = client.get(f'/nodes/{response.json()["uuid"]}/repo/metadata')
    assert check.status_code == 200, check.content
    result = check.json()
    assert 'test_file.txt' in result
    assert result['test_file.txt']['type'] == 'FILE'
    assert result['test_file.txt']['size'] == len(b'Some test strings')
    assert result['test_file.txt']['binary'] is False


@pytest.mark.usefixtures('authenticate')
def test_create_single_file_binary(client: TestClient):
    """Testing binary file upload"""
    binary_content = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
    files = [
        (
            'files',
            (
                'binary_file.bin',
                io.BytesIO(binary_content),
                'application/octet-stream',
            ),
        )
    ]
    data = {
        'params': json.dumps(
            {
                'node_type': 'data.core.singlefile.SinglefileData.',
            }
        )
    }

    response = client.post('/nodes/file-upload', files=files, data=data)
    assert response.status_code == 200, response.json()

    check = client.get(f'/nodes/{response.json()["uuid"]}/repo/metadata')
    assert check.status_code == 200, check.content
    result = check.json()
    assert 'binary_file.bin' in result
    assert result['binary_file.bin']['type'] == 'FILE'
    assert result['binary_file.bin']['size'] == len(binary_content)
    assert result['binary_file.bin']['binary'] is True


@pytest.mark.usefixtures('authenticate')
def test_create_folder_data(client: TestClient):
    """Testing folder upload"""
    files = [
        (
            'files',
            (
                'folder/file1.txt',
                io.BytesIO(b'Content of file 1'),
                'text/plain',
            ),
        ),
        (
            'files',
            (
                'folder/file2.txt',
                io.BytesIO(b'Content of file 2'),
                'text/plain',
            ),
        ),
    ]
    data = {
        'params': json.dumps(
            {
                'node_type': 'data.core.folder.FolderData.',
            }
        )
    }

    response = client.post('/nodes/file-upload', files=files, data=data)
    assert response.status_code == 200, response.json()

    check = client.get(f'/nodes/{response.json()["uuid"]}/repo/metadata')
    assert check.status_code == 200, check.content
    result = check.json()
    assert 'folder' in result
    assert result['folder']['type'] == 'DIRECTORY'
    assert 'objects' in result['folder']
    objects = result['folder']['objects']
    assert len(objects) == 2
    for file in files:
        filename = file[1][0].split('/', 1)[1]
        assert filename in objects
        assert objects[filename]['type'] == 'FILE'
        expected_size = len(file[1][1].getvalue())
        assert objects[filename]['size'] == expected_size
        assert objects[filename]['binary'] is False


@pytest.mark.usefixtures('authenticate')
def test_create_node_with_files_has_zipped_metadata(client: TestClient):
    """Test link for zipped repo content is present when creating node with files."""
    files = [
        (
            'files',
            (
                'file1.txt',
                io.BytesIO(b'Content of file 1'),
                'text/plain',
            ),
        ),
        (
            'files',
            (
                'file2.txt',
                io.BytesIO(b'Content of file 2'),
                'text/plain',
            ),
        ),
    ]
    data = {
        'params': json.dumps(
            {
                'node_type': 'data.core.int.Int.',
                'attributes': {'value': 42},
            }
        )
    }

    response = client.post('/nodes/file-upload', files=files, data=data)
    assert response.status_code == 200, response.json()

    check = client.get(f'/nodes/{response.json()["uuid"]}/repo/metadata')
    assert check.status_code == 200, check.content
    result = check.json()
    assert 'zipped' in result
    assert result['zipped']['type'] == 'FILE'
    assert result['zipped']['binary'] is True
    assert result['zipped']['size'] == sum(len(file[1][1].getvalue()) for file in files)


@pytest.mark.parametrize(
    'node_type, value',
    [
        ('data.core.int.Int.', 'test'),
        ('data.core.float.Float.', [1, 2, 3]),
        ('data.core.str.Str.', 5),
    ],
)
@pytest.mark.usefixtures('authenticate')
def test_create_node_wrong_value(client: TestClient, node_type: str, value: t.Any):
    """Test creating a new node with wrong value."""
    response = client.post(
        '/nodes',
        json={
            'node_type': node_type,
            'attributes': {'value': value},
        },
    )
    assert response.status_code == 422, response.content


@pytest.mark.usefixtures('default_computers', 'authenticate')
def test_create_unknown_entry_point(client: TestClient):
    """Test error message when specifying unknown ``entry_point``."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.nonexistent.NonExistentType.',
            'label': 'test_code',
        },
    )
    assert response.status_code == 422, response.content


@pytest.mark.usefixtures('default_computers', 'authenticate')
def test_create_additional_attribute(client: TestClient):
    """Test adding additional properties are ignored."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.int.Int.',
            'attributes': {
                'value': 5,
                'extra_thing': 'should_not_be_here',
            },
        },
    )
    assert response.status_code == 200, response.content

    check = client.get(f'/nodes/{response.json()["uuid"]}/attributes')
    assert check.status_code == 200, check.content
    result = check.json()
    assert 'value' in result
    assert 'extra_thing' not in result


@pytest.mark.usefixtures('authenticate')
def test_create_bool_with_extra(client: TestClient):
    """Test creating a new Bool with extra."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.bool.Bool.',
            'attributes': {'value': True},
            'extras': {'extra_one': 'value_1', 'extra_two': 'value_2'},
        },
    )
    assert response.status_code == 200, response.content

    # We exclude extras from the node response, so we check by retrieving them separately
    check = client.get(f'/nodes/{response.json()["uuid"]}/extras')
    assert check.status_code == 200, check.content
    result = check.json()
    assert result['extra_one'] == 'value_1'
    assert result['extra_two'] == 'value_2'


@pytest.mark.anyio
async def test_get_download_node(async_client: AsyncClient, array_data_node: orm.ArrayData):
    """Test download node /nodes/{nodes_id}/download.
    The async client is needed to avoid an error caused by an I/O operation on closed file"""

    # Test that array is correctly downloaded as json
    response = await async_client.get(f'/nodes/{array_data_node.pk}/download?download_format=json')
    assert response.status_code == 200, response.json()
    assert response.json().get('default', None) == array_data_node.get_array().tolist()

    # Test exception when wrong download format given
    response = await async_client.get(f'/nodes/{array_data_node.pk}/download?download_format=cif')
    assert response.status_code == 422, response.json()
    assert 'format cif is not supported' in response.json()['detail']

    # Test exception when no download format given
    response = await async_client.get(f'/nodes/{array_data_node.pk}/download')
    assert response.status_code == 422, response.json()
    assert 'Please specify the download format' in response.json()['detail']


@pytest.mark.usefixtures('default_nodes')
@pytest.mark.anyio
async def test_get_statistics(async_client: AsyncClient):
    """Test get statistics for nodes."""

    from datetime import datetime

    default_user_reference_json = {
        'total': 4,
        'types': {
            'data.core.float.Float.': 1,
            'data.core.str.Str.': 1,
            'data.core.bool.Bool.': 1,
            'data.core.int.Int.': 1,
        },
        'ctime_by_day': {datetime.today().strftime('%Y-%m-%d'): 4},
    }

    # Test without specifying user, should use default user
    response = await async_client.get('/nodes/statistics')
    assert response.status_code == 200, response.json()
    assert response.json() == default_user_reference_json

    # Test that the output is the same when we use the pk of the default user
    from aiida import orm

    default_user_pk = orm.User(email='').collection.get_default().pk
    response = await async_client.get(f'/nodes/statistics?user={default_user_pk}')
    assert response.status_code == 200, response.json()
    assert response.json() == default_user_reference_json

    # Test empty response for nonexisting user
    response = await async_client.get('/nodes/statistics?user=99999')
    assert response.status_code == 200, response.json()
    assert response.json() == {'total': 0, 'types': {}, 'ctime_by_day': {}}
