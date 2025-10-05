"""Declaration of FastAPI router for nodes."""

from __future__ import annotations

import io
import json
import tempfile
import typing as t
from pathlib import Path

import pydantic as pdt
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import EntryPointError
from aiida.common.exceptions import LicensingException, NotExistent
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from aiida_restapi import resources
from aiida_restapi.common import NodeModelRegistry, NodeRepository, PaginatedResults, QueryParams, query_params

from .auth import get_current_active_user

router = APIRouter()


repository = NodeRepository[orm.Node, orm.Node.Model](orm.Node)
model_registry = NodeModelRegistry()


@router.get(
    '/nodes',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_nodes(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Node.Model]:
    """Get AiiDA nodes with optional filtering, sorting, and/or pagination."""
    return repository.get_entities(queries)


@router.get('/nodes/projectable_properties')
@with_dbenv()
async def get_node_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA nodes."""
    return repository.get_projectable_properties()


@router.get('/nodes/types')
async def get_nodes_types() -> list[str]:
    """Get available AiiDA node class names."""
    return sorted(model_registry.get_node_types())


@router.get(
    '/nodes/types/{node_class}',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_nodes_by_type(
    node_class: str,
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Node.Model]:
    """Get AiiDA nodes by node type with optional filtering, sorting, and/or pagination."""
    if (node_type := model_registry.get_node_type(node_class)) is None:
        raise HTTPException(status_code=404, detail=f'Node class `{node_class}` is not recognized.')
    queries.filters['node_type'] = {'like': node_type}
    return repository.get_entities(queries)


@router.get('/nodes/types/{node_class}/projectable_properties')
@with_dbenv()
async def get_node_class_projectable_properties(node_class: str) -> list[str]:
    """Get projectable properties of a given AiiDA node class."""
    return repository.get_projectable_properties(node_class)


@router.get('/nodes/types/{node_class}/schema')
@with_dbenv()
async def get_node_class_schema(node_class: str) -> dict[str, t.Any]:
    """Get JSON schema for a given AiiDA node class."""
    if (NodeModel := model_registry.get_model(node_class)) is None:
        raise HTTPException(status_code=404, detail=f'Node class `{node_class}` is not recognized.')
    return NodeModel.model_json_schema()


@router.get(
    '/nodes/{node_id}',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_node(node_id: int) -> orm.Node.Model:
    """Get AiiDA node by id."""
    return repository.get_entity_by_id(node_id)


@router.get('/nodes/download_formats')
async def get_nodes_download_formats() -> dict[str, t.Any]:
    """Get download formats for AiiDA nodes."""
    return resources.get_all_download_formats()


@router.get('/nodes/{node_id}/download')
@with_dbenv()
async def download_node(
    node_id: int,
    download_format: str | None = Query(None, description='Format to download the node in'),
) -> StreamingResponse:
    """Download AiiDA node by id in a given download format (provided as a query parameter)."""
    try:
        node = orm.load_node(node_id)
    except NotExistent:
        raise HTTPException(status_code=404, detail=f'Could not find any node with id {node_id}')

    if download_format is None:
        raise HTTPException(
            status_code=422,
            detail='Please specify the download format. '
            'The available download formats can be '
            'queried using the /nodes/download_formats/ endpoint.',
        )

    elif download_format in node.get_export_formats():
        # byteobj, dict with {filename: filecontent}

        try:
            exported_bytes, _ = node._exportcontent(download_format)
        except LicensingException as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        def stream() -> t.Generator[bytes, None, None]:
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


@router.post(
    '/nodes',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_node(
    node_model: model_registry.ModelUnion,  # type: ignore
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Create new AiiDA node."""
    try:
        return repository.create_entity(node_model)
    except EntryPointError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except (TypeError, ValueError, KeyError) as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


# TODO what about folderdata?
@router.post(
    '/nodes/singlefile',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_upload_file(
    params: t.Annotated[str, Form()],
    upload_file: UploadFile,
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Endpoint for uploading file data

    Note that in this multipart form case, json input can't be used.
    Get the parameters as a string and manually pass through pydantic.
    """
    try:
        # Parse the JSON string into a dictionary
        params_dict = json.loads(params)
        # Validate against the Pydantic model
        params_model = orm.Node.Model(**params_dict)
    except json.JSONDecodeError as exception:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid JSON format: {exception!s}',
        ) from exception
    except pdt.ValidationError as exception:
        raise HTTPException(
            status_code=422,
            detail=f'Validation failed: {exception}',
        ) from exception

    try:
        cls = orm.utils.load_node_class(params_model.node_type)
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

    temp_file_path = Path(temp_path)
    node_dict = params_model.model_dump(exclude_unset=True, exclude_none=True)
    orm_entity = repository.create_node_with_file(cls, node_dict, temp_file_path)

    # Clean up the temporary file
    if temp_file_path.exists():
        temp_file_path.unlink()

    return orm_entity.to_model()
