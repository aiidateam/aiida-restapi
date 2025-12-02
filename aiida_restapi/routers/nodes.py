"""Declaration of FastAPI application."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Generator, List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import EntryPointError, LicensingException, NotExistent
from aiida.plugins.entry_point import load_entry_point
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from aiida_restapi import models, resources
from aiida_restapi.identifiers import get_node_namespace

from .auth import get_current_active_user

router = APIRouter()


@router.get('/nodes', response_model=List[models.Node])
@with_dbenv()
async def read_nodes() -> List[models.Node]:
    """Get list of all nodes"""
    return models.Node.get_entities()


@router.get('/nodes/projectable_properties', response_model=List[str])
async def get_nodes_projectable_properties() -> List[str]:
    """Get projectable properties for nodes endpoint"""

    return models.Node.get_projectable_properties()


@router.get('/nodes/download_formats', response_model=dict[str, Any])
async def get_nodes_download_formats() -> dict[str, Any]:
    """Get download formats for nodes endpoint"""

    return resources.get_all_download_formats()


@router.get('/nodes/{nodes_id}/download')
@with_dbenv()
async def download_node(nodes_id: int, download_format: Optional[str] = None) -> StreamingResponse:
    """Get nodes by id."""
    from aiida.orm import load_node

    try:
        node = load_node(nodes_id)
    except NotExistent:
        raise HTTPException(status_code=404, detail=f'Could no find any node with id {nodes_id}')

    if download_format is None:
        raise HTTPException(
            status_code=422,
            detail='Please specify the download format. '
            'The available download formats can be '
            'queried using the /nodes/download_formats/ endpoint.',
        )

    elif download_format in node.get_export_formats():
        # byteobj, dict with {filename: filecontent}
        import io

        try:
            exported_bytes, _ = node._exportcontent(download_format)
        except LicensingException as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        def stream() -> Generator[bytes, None, None]:
            with io.BytesIO(exported_bytes) as handler:
                yield from handler

        return StreamingResponse(stream(), media_type=f'application/{download_format}')

    else:
        raise HTTPException(
            status_code=422,
            detail='The format {} is not supported. '
            'The available download formats can be '
            'queried using the /nodes/download_formats/ endpoint.'.format(download_format),
        )


@router.get('/nodes/full_types', response_model=dict[str, Any])
@with_dbenv()
async def get_full_types() -> dict[str, Any]:
    """Return full_types of the nodes"""
    return get_node_namespace(user_pk=None, count_nodes=False).get_description()


@router.get('/nodes/{nodes_id}', response_model=models.Node)
@with_dbenv()
async def read_node(nodes_id: int) -> Optional[models.Node]:
    """Get nodes by id."""
    qbobj = orm.QueryBuilder()
    qbobj.append(orm.Node, filters={'id': nodes_id}, project='**', tag='node').limit(1)
    return qbobj.dict()[0]['node']


@router.post('/nodes', response_model=models.Node)
@with_dbenv()
async def create_node(
    node: models.Node_Post,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Node:
    """Create new AiiDA node."""
    node_dict = node.dict(exclude_unset=True)
    entry_point = node_dict.pop('entry_point', None)

    try:
        cls = load_entry_point(group='aiida.data', name=entry_point)
    except EntryPointError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception

    try:
        orm_object = models.Node_Post.create_new_node(cls, node_dict)
    except (TypeError, ValueError, KeyError) as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception

    return models.Node.from_orm(orm_object)


@router.post('/nodes/singlefile', response_model=models.Node)
@with_dbenv()
async def create_upload_file(
    params: str = Form(...),
    upload_file: UploadFile = File(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Node:
    """Endpoint for uploading file data

    Note that in this multipart form case, json input can't be used.
    Get the parameters as a string and manually pass through pydantic.
    """
    try:
        # Parse the JSON string into a dictionary
        params_dict = json.loads(params)
        # Validate against the Pydantic model
        params_obj = models.Node_Post(**params_dict)
    except json.JSONDecodeError as exception:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid JSON format: {exception!s}',
        ) from exception
    except ValidationError as exception:
        raise HTTPException(
            status_code=422,
            detail=f'Validation failed: {exception}',
        ) from exception

    node_dict = params_obj.dict(exclude_unset=True)
    entry_point = node_dict.pop('entry_point', None)

    try:
        cls = load_entry_point(group='aiida.data', name=entry_point)
    except EntryPointError as exception:
        raise HTTPException(
            status_code=404,
            detail=f'Could not load entry point: {exception}',
        ) from exception

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
        # Todo: read in chunks
        content = await upload_file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    orm_object = models.Node_Post.create_new_node_with_file(cls, node_dict, Path(temp_path))

    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)

    return models.Node.from_orm(orm_object)
