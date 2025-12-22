"""Test the /processes endpoint"""

import io

import pytest
from aiida import orm


@pytest.mark.anyio
async def test_add_process(default_test_add_process, async_client, authenticate):  # pylint: disable=unused-argument
    """Test adding new process"""
    code_id, x_id, y_id = default_test_add_process
    response = await async_client.post(
        '/submit',
        json={
            'label': 'test_new_process',
            'entry_point': 'aiida.calculations:core.arithmetic.add',
            'inputs': {
                'code.uuid': code_id,
                'x.uuid': x_id,
                'y.uuid': y_id,
                'metadata': {
                    'description': 'Test job submission with the add plugin',
                },
            },
        },
    )
    assert response.status_code == 200


def test_add_process_invalid_entry_point(default_test_add_process, client, authenticate):  # pylint: disable=unused-argument
    """Test adding new process with invalid entry point"""
    code_id, x_id, y_id = default_test_add_process
    response = client.post(
        '/submit',
        json={
            'label': 'test_new_process',
            'entry_point': 'wrong_entry_point',
            'inputs': {
                'code.uuid': code_id,
                'x.uuid': x_id,
                'y.uuid': y_id,
                'metadata': {
                    'description': 'Test job submission with the add plugin',
                },
            },
        },
    )
    assert response.status_code == 404


def test_add_process_invalid_node_id(default_test_add_process, client, authenticate):  # pylint: disable=unused-argument
    """Test adding new process with invalid Node ID"""
    code_id, x_id, _ = default_test_add_process
    response = client.post(
        '/submit',
        json={
            'label': 'test_new_process',
            'entry_point': 'aiida.calculations:core.arithmetic.add',
            'inputs': {
                'code.uuid': code_id,
                'x.uuid': x_id,
                'y.uuid': '891a9efa-f90e-11eb-9a03-0242ac130003',
                'metadata': {
                    'description': 'Test job submission with the add plugin',
                },
            },
        },
    )
    assert response.status_code == 404
    assert response.json() == {'detail': 'Node with UUID `891a9efa-f90e-11eb-9a03-0242ac130003` does not exist.'}


@pytest.mark.anyio
async def test_add_process_nested_inputs(default_test_add_process, async_client, authenticate):  # pylint: disable=unused-argument
    """Test adding new process that has nested inputs"""
    code_id, _, _ = default_test_add_process
    template = orm.Dict(
        {
            'files_to_copy': [('file', 'file.txt')],
        }
    ).store()
    single_file = orm.SinglefileData(io.StringIO('content')).store()

    response = await async_client.post(
        '/submit',
        json={
            'label': 'test_new_process',
            'entry_point': 'aiida.calculations:core.templatereplacer',
            'inputs': {
                'code.uuid': code_id,
                'template.uuid': template.uuid,
                'files': {'file.uuid': single_file.uuid},
                'metadata': {
                    'description': 'Test job submission with the add plugin',
                    'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}},
                },
            },
        },
    )
    assert response.status_code == 200
