"""Test the /nodes endpoint"""

import io
import json

import pytest
from aiida import orm


def test_get_node_projectable_properties(client):
    """Test get projectable properties for nodes."""
    response = client.get('/nodes/projectable_properties')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Node.fields.keys())


def test_get_nodes(default_nodes, client):  # pylint: disable=unused-argument
    """Test listing existing nodes."""
    response = client.get('/nodes')
    assert response.status_code == 200
    assert len(response.json()['results']) == 4
    result = response.json()['results'][0]
    assert not result['attributes']
    assert not result['extras']


def test_get_node(default_nodes, client):  # pylint: disable=unused-argument
    """Test retrieving a single nodes."""
    for nodes_id in default_nodes:
        response = client.get(f'/nodes/{nodes_id}')
        assert response.status_code == 200
        result = response.json()
        assert not result['attributes']
        assert not result['extras']


def test_get_download_formats(client):
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


def test_get_node_repository_metadata(array_data_node, client):
    """Test retrieving repository metadata for a node."""
    response = client.get(f'/nodes/{array_data_node.pk}/repo/metadata')
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


def test_create_dict(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new dict."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.dict.Dict',
            'value': {'x': 1, 'y': 2},
            'label': 'test_dict',
        },
    )
    assert response.status_code == 200, response.content


@pytest.mark.anyio
async def test_create_code(default_computers, async_client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Code."""
    for comp_id in default_computers:
        response = await async_client.post(
            '/nodes',
            json={
                'node_type': 'data.core.code.installed.InstalledCode',
                'computer': comp_id,
                'filepath_executable': '/bin/true',
                'label': 'test_code',
            },
        )
    assert response.status_code == 200, response.content


def test_create_list(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new list."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.list.List',
            'value': [2, 3],
        },
    )
    assert response.status_code == 200, response.content


def test_create_int(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Int."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.int.Int',
            'value': 6,
        },
    )
    assert response.status_code == 200, response.content


def test_create_float(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Float."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.float.Float',
            'value': 6.6,
        },
    )
    assert response.status_code == 200, response.content


def test_create_string(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new string."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.str.Str',
            'value': 'test_string',
        },
    )
    assert response.status_code == 200, response.content


def test_create_bool(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Bool."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.bool.Bool',
            'value': 'True',
        },
    )
    assert response.status_code == 200, response.content


def test_create_structure_data(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new StructureData."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.structure.StructureData',
            'description': '',
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
    )
    assert response.status_code == 200, response.content


def test_create_orbital_data(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new OrbitalData."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.orbital.OrbitalData',
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


def test_create_single_file_upload(client, authenticate):  # pylint: disable=unused-argument
    """Testing file upload"""
    test_file = {
        'upload_file': (
            'test_file.txt',
            io.BytesIO(b'Some test strings'),
            'multipart/form-data',
        )
    }
    data = {
        'params': json.dumps(
            {
                'node_type': 'data.core.singlefile.SinglefileData',
                'description': 'Testing single upload file',
                'filename': 'test_file.txt',
            }
        )
    }

    response = client.post('/nodes/file-upload', files=test_file, data=data)
    assert response.status_code == 200, response.json()


@pytest.mark.parametrize(
    'node_type, value',
    [
        ('data.core.int.Int', 'test'),
        ('data.core..float.Float', [1, 2, 3]),
        ('data.core.str.Str', 5),
    ],
)
def test_create_node_wrong_value(client, node_type, value, authenticate):  # pylint: disable=unused-argument
    """Test creating a new node with wrong value."""
    response = client.post(
        '/nodes',
        json={
            'node_type': node_type,
            'value': value,
        },
    )
    assert response.status_code == 422, response.content


def test_create_unknown_entry_point(default_computers, client, authenticate):  # pylint: disable=unused-argument
    """Test error message when specifying unknown ``entry_point``."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.nonexistent.NonExistentType',
            'label': 'test_code',
        },
    )
    assert response.status_code == 422, response.content


def test_create_additional_attribute(default_computers, client, authenticate):  # pylint: disable=unused-argument
    """Test adding additional properties are ignored."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.int.Int',
            'value': 42,
            'extra_thing': 'should be ignored',
        },
    )
    assert response.status_code == 200, response.content
    assert 'extra_thing' not in response.json().get('attributes', {})


def test_create_bool_with_extra(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new Bool with extra."""
    response = client.post(
        '/nodes',
        json={
            'node_type': 'data.core.bool.Bool',
            'value': 'True',
            'extras': {'extra_one': 'value_1', 'extra_two': 'value_2'},
        },
    )
    assert response.status_code == 200, response.content
    assert not response.json()['extras']

    # We exclude extras from the node response, so we check by retrieving them separately
    response = client.get(f'/nodes/{response.json()["pk"]}/extras')
    assert response.status_code == 200
    assert response.json()['extra_one'] == 'value_1'
    assert response.json()['extra_two'] == 'value_2'


@pytest.mark.anyio
async def test_get_download_node(array_data_node, async_client):
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
