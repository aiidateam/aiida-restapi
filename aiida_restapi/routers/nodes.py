"""Declaration of FastAPI router for nodes."""

from __future__ import annotations

import io
import json
import typing as t

import pydantic as pdt
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import LicensingException, NotExistent
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from aiida_restapi import resources
from aiida_restapi.common import NodeModelRegistry, NodeRepository, PaginatedResults, QueryParams, query_params

from .auth import UserInDB, get_current_active_user

router = APIRouter()


repository = NodeRepository[orm.Node, orm.Node.Model](orm.Node)
model_registry = NodeModelRegistry()


@router.get('/nodes/schema')
async def get_nodes_schema(
    which: t.Literal['get', 'post'] | None = Query(
        None,
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA nodes.

    :param which: The type of schema to retrieve: 'get' or 'post'.
    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    :raises: HTTPException: If the 'which' parameter is not 'get' or 'post'.
    """

    def generate_create_models() -> dict[str, dict[str, t.Any]]:
        return {model.__name__: model.model_json_schema() for model in model_registry.get_models()}

    if which is None:
        return {
            'get': orm.Node.Model.model_json_schema(),
            'post': generate_create_models(),
        }
    if which == 'get':
        return orm.Node.Model.model_json_schema()
    if which == 'post':
        return generate_create_models()
    raise HTTPException(
        status_code=404,
        detail=f'Schema type "{which}" not supported; expected "get" or "post"',
    )


@router.get('/nodes/projectable_properties')
@with_dbenv()
async def get_node_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA nodes.

    :return: The list of projectable properties for AiiDA nodes.
    """
    return repository.get_projectable_properties()


@router.get('/nodes/download_formats')
async def get_nodes_download_formats() -> dict[str, t.Any]:
    """Get download formats for AiiDA nodes.

    :return: A dictionary with available download formats as keys and their descriptions as values.
    """
    return resources.get_all_download_formats()


@router.get(
    '/nodes',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_nodes(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Node.Model]:
    """Get AiiDA nodes with optional filtering, sorting, and/or pagination.

    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of node models.
    """
    return repository.get_entities(queries)


@router.get('/nodes/types')
async def get_nodes_types() -> list:
    """
    Return all node types in a machine-actionable format:

    >>> [
    >>>   {
    >>>     "label": "Int",
    >>>     "node_type": "data.core.int.Int.",
    >>>     "nodes": "/nodes/types/data.core.int.Int"
    >>>     "projections": "/nodes/types/data.core.int.Int/projectable_properties",
    >>>     "schema": "/nodes/types/data.core.int.Int/schema",
    >>>   },
    >>>   ...
    >>> ]
    """
    return [
        {
            'label': model_registry.get_node_class_name(node_type),
            'node_type': f'{node_type}.',
            'nodes': f'/nodes/types/{node_type}',
            'projections': f'/nodes/types/{node_type}/projectable_properties',
            'schema': f'/nodes/types/{node_type}/schema',
        }
        for node_type in sorted(
            model_registry.get_node_types(), key=lambda node_type: model_registry.get_node_class_name(node_type)
        )
    ]


@router.get(
    '/nodes/types/{node_type}',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_nodes_by_type(
    node_type: str,
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Node.Model]:
    """Get AiiDA nodes by node type with optional filtering, sorting, and/or pagination.

    :param node_type: The AiiDA node type string.
    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of node models.
    :raises HTTPException: If the node class is not recognized (404), or on failure (400).
    """
    try:
        queries.filters['node_type'] = {'like': f'%{node_type}%'}
        return repository.get_entities(queries)
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


@router.get('/nodes/types/{node_type}/projectable_properties')
@with_dbenv()
async def get_node_class_projectable_properties(node_type: str) -> list[str]:
    """Get projectable properties of a given AiiDA node class.

    :param node_type: The AiiDA node type string.
    :return: The list of projectable properties for the given AiiDA node class.
    :raises HTTPException: If the node class is not recognized (404), or on failure (400).
    """
    try:
        return repository.get_projectable_properties(node_type)
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


@router.get('/nodes/types/{node_type}/schema')
async def get_node_class_schema(
    node_type: str,
    which: t.Literal['get', 'post'] | None = Query(
        None,
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict[str, t.Any]:
    """Get JSON schema for a given AiiDA node class.

    :param node_type: The AiiDA node type string.
    :param which: The type of schema to retrieve: 'get' or 'post'.
    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    :raises HTTPException: If the node class (or `which` parameter) is not recognized (404), or on failure (400).
    """
    try:
        NodeModel = model_registry.get_model(node_type)
        if which is None:
            return {
                'get': orm.Node.Model.model_json_schema(),
                'post': NodeModel.model_json_schema(),
            }
        if which == 'get':
            return orm.Node.Model.model_json_schema()
        if which == 'post':
            return NodeModel.model_json_schema()
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception
    raise HTTPException(status_code=404, detail='Parameter "which" must be either "get" or "post"')


@router.get(
    '/nodes/{node_id}',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_node(node_id: int) -> orm.Node.Model:
    """Get AiiDA node by id.

    :param node_id: The id of the node to retrieve.
    :return: The AiiDA node model, e.g. `orm.Node.Model`,
    :raises HTTPException: If the node with the given id does not exist.
    """
    try:
        return repository.get_entity_by_id(node_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f'Could not find any Node with id {node_id}')


@router.get('/nodes/{node_id}/download')
@with_dbenv()
async def download_node(
    node_id: int,
    download_format: str | None = Query(None, description='Format to download the node in'),
) -> StreamingResponse:
    """Download AiiDA node by id in a given download format provided as a query parameter.

    :param node_id: The id of the node to retrieve.
    :param download_format: The format to download the node in.
    :return: StreamingResponse with the exported node content.
    :raises HTTPException: If the node with the given id does not exist (404),
        if the download format is not specified (422),
        or if the download format is not supported (422).
    """
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


@router.get('/nodes/{node_id}/repo/contents')
@with_dbenv()
async def get_node_repo_file_contents(
    node_id: int,
    filename: str | None = Query(None, description='Filename of repository content to retrieve'),
) -> StreamingResponse:
    """Get the repository contents of a node.

    :param node_id: The id of the node to retrieve the repository contents for.
    :param filename: The filename of the repository content to retrieve. If None, retrieves all contents.
    :return: StreamingResponse with the requested file content.
    :raises HTTPException: If the node with the given id does not exist (404),
        or if the requested file does not exist in the node's repository (404).
    """
    try:
        node = orm.load_node(node_id)
    except NotExistent:
        raise HTTPException(status_code=404, detail=f'Could not find any node with id {node_id}')

    repo = node.base.repository

    if filename:
        if filename not in repo.list_object_names():
            raise HTTPException(
                status_code=404,
                detail=f'Could not find file {filename} in the repository of node with id {node_id}',
            )

        file_content = repo.get_object_content(filename, mode='rb')

        def file_stream() -> t.Generator[bytes, None, None]:
            with io.BytesIO(file_content) as handler:
                yield from handler

        return StreamingResponse(file_stream(), media_type='application/octet-stream')

    else:
        zip_bytes = repo.get_zipped_objects()

        def zip_stream() -> t.Generator[bytes, None, None]:
            with io.BytesIO(zip_bytes) as handler:
                yield from handler

        return StreamingResponse(zip_stream(), media_type='application/zip')


@router.post(
    '/nodes',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_node(
    node_model: model_registry.ModelUnion,  # type: ignore
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Create new AiiDA node.

    :param node_model: The AiiDA ORM model of the node to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA node.
    :raises HTTPException: If the node class is not recognized (404),
        or if creation fails (400).
    """
    try:
        return repository.create_entity(node_model)
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


# TODO what about folderdata?
@router.post(
    '/nodes/file-upload',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_upload_file(
    params: t.Annotated[str, Form()],
    upload_file: UploadFile,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Create new AiiDA node with uploaded file.

    :param params: JSON string of the node parameters.
    :param upload_file: The file to upload.
    :param current_user: The current authenticated user.
    :return: The created AiiDA node model.
    :raises HTTPException: If the JSON is invalid (400), if the node class is not recognized (404),
        or if validation fails (422).
    """
    # Note that in this multipart form case, json input can't be used.
    # Here instead we get the parameters as a string and manually pass through pydantic.
    try:
        params_dict = t.cast(dict, json.loads(params))
        params_dict['content'] = await upload_file.read()  # TODO: read in chunks
        node_type = params_dict.get('node_type', 'data.core.singlefile.SinglefileData')
        node_model = model_registry.get_model(node_type)
        model = node_model(**params_dict)
    except json.JSONDecodeError as exception:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid JSON format: {exception!s}',
        ) from exception
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except pdt.ValidationError as exception:
        raise HTTPException(
            status_code=422,
            detail=f'Validation failed: {exception}',
        ) from exception
    return repository.create_entity(model)
