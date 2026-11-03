"""Test the /processes endpoint"""

import io
from unittest.mock import patch

import pytest
from aiida import orm
from fastapi.testclient import TestClient
from httpx import AsyncClient

from aiida_restapi.models.process import SubmittedProcess
from aiida_restapi.routers.submit import _process_inputs


def test_submitted_process_keeps_uuid_inputs_unresolved():
    inputs = {
        'structure.uuid': 'structure-uuid',
        'pseudos': {'Si.uuid': 'pseudo-uuid'},
    }

    with patch('aiida_restapi.routers.submit.orm.load_node') as load_node:
        process = SubmittedProcess(
            entry_point='aiida.workflows:aiidalab_qe.app',
            inputs=inputs,
        )

    load_node.assert_not_called()
    assert process.inputs == inputs


def test_process_input_resolution_recurses_into_uuid_references():
    structure = object()
    pseudo = object()
    inputs = {
        'structure.uuid': 'structure-uuid',
        'pseudos': {'Si.uuid': 'pseudo-uuid'},
    }

    with patch(
        'aiida_restapi.routers.submit.orm.load_node',
        side_effect=[structure, pseudo],
    ) as load_node:
        assert _process_inputs(inputs) == {
            'structure': structure,
            'pseudos': {'Si': pseudo},
        }

    assert load_node.call_count == 2


@pytest.mark.anyio
async def test_submit_resolves_uuid_inputs_in_route(async_client, default_test_add_process):
    code_id, x_id, y_id = default_test_add_process
    process_node = orm.load_node(x_id)

    with patch(
        'aiida_restapi.routers.submit.engine.submit',
        return_value=process_node,
    ) as submit:
        response = await async_client.post(
            '/submit',
            json={
                'entry_point': 'aiida.calculations:core.arithmetic.add',
                'inputs': {
                    'code.uuid': code_id,
                    'x.uuid': x_id,
                    'y.uuid': y_id,
                },
            },
        )

    assert response.status_code == 200
    submitted_inputs = submit.call_args.kwargs
    assert submitted_inputs['code'].uuid == code_id
    assert submitted_inputs['x'].uuid == x_id
    assert submitted_inputs['y'].uuid == y_id


@pytest.mark.anyio
async def test_add_process(async_client: AsyncClient, default_test_add_process: list[str]):
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


def test_add_process_invalid_entry_point(client: TestClient, default_test_add_process: list[str]):
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
    assert response.status_code == 422


def test_add_process_invalid_node_id(client: TestClient, default_test_add_process):
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
    error = response.json()['errors'][0]
    assert 'no Node found with UUID<891a9efa-f90e-11eb-9a03-0242ac130003>' in error['detail']


@pytest.mark.anyio
async def test_add_process_nested_inputs(async_client: AsyncClient, default_test_add_process):
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
