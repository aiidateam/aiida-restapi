"""Declaration of FastAPI router for nodes."""

from __future__ import annotations

import io
import json
import typing as t

import pydantic as pdt
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import EntryPointError, LicensingException, NotExistent
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from typing_extensions import TypeAlias

from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryParams, query_params
from aiida_restapi.config import API_CONFIG
from aiida_restapi.models.node import MetadataType, NodeModelRegistry, NodeStatistics, NodeType
from aiida_restapi.services.node import NodeLink, NodeService

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/nodes')
write_router = APIRouter(prefix='/nodes')

service = NodeService[orm.Node, orm.Node.Model](orm.Node)

model_registry = NodeModelRegistry()

if t.TYPE_CHECKING:
    # Dummy type for static analysis
    NodeModelUnion: TypeAlias = pdt.BaseModel
else:
    # The real discriminated union built at runtime
    NodeModelUnion = model_registry.ModelUnion


@read_router.get(
    '/schema',
    response_model=dict,
)
async def get_nodes_schema(
    node_type: str | None = Query(
        None,
        description='The AiiDA node type string.',
        alias='type',
    ),
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='The type of schema to retrieve: "get" for the response model, "post" for the creation model.',
    ),
) -> dict:
    """Get JSON schema for the base AiiDA node 'get' model.

    :param node_type: The AiiDA node type string.
    :param which: The type of schema to retrieve: 'get' or 'post'.
    :return: The JSON schema for the base AiiDA node 'get' model.
    :raises HTTPException: 422 if the 'which' parameter is not 'get' or 'post',
        422 if the node type is not recognized,
        500 for any other failures.
    """
    if not node_type:
        return orm.Node.Model.model_json_schema()
    try:
        model = model_registry.get_model(node_type, which)
        return model.model_json_schema()
    except KeyError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/projections',
    response_model=list[str],
)
@with_dbenv()
async def get_node_projections(
    node_type: str | None = Query(
        None,
        description='The AiiDA node type string.',
        alias='type',
    ),
) -> list[str]:
    """Get queryable projections for AiiDA nodes.

    :param node_type: The AiiDA node type string.
    :return: The list of queryable projections for AiiDA nodes.
    :raises HTTPException: 422 if the node type is not recognized,
        500 for any other failures.
    """
    try:
        return service.get_projections(node_type)
    except ValueError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/statistics',
    response_model=NodeStatistics,
)
@with_dbenv()
async def get_nodes_statistics(user: int | None = None) -> dict[str, t.Any]:
    """Get node statistics.

    :param user: Optional user PK to filter statistics by user.
    :return: A dictionary containing total node count, counts by node type, and creation time statistics.

    >>> {
    >>>   "total": 47,
    >>>   "types": {
    >>>       "data.core.int.Int.": 42,
    >>>       "data.core.singlefile.SinglefileData.": 5,
    >>>       ...
    >>>   },
    >>>   "ctime_by_day": {
    >>>       "2012-01-01": 10,
    >>>       "2012-01-02": 15,
    >>>       ...
    >>>   },
    >>> }
    """

    from aiida.manage import get_manager

    backend = get_manager().get_profile_storage()
    return backend.query().get_creation_statistics(user_pk=user)


@read_router.get('/download_formats')
async def get_nodes_download_formats() -> dict[str, t.Any]:
    """Get download formats for AiiDA nodes.

    :return: A dictionary with available download formats as keys and their descriptions as values.
    :raises HTTPException: 404 if the download formats are not available,
        500 for other failures during retrieval.
    """
    try:
        return service.get_download_formats()
    except EntryPointError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_nodes(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Node.Model]:
    """Get AiiDA nodes with optional filtering, sorting, and/or pagination.

    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of node models.
    """
    return service.get_many(queries)


@read_router.get(
    '/types',
    response_model=list[NodeType],
)
async def get_node_types() -> list:
    """Get all node types in machine-actionable format.

    :return: A list of dictionaries, each containing information about a node type, e.g.:

    >>> [
    >>>   {
    >>>     "label": "Int",
    >>>     "node_type": "data.core.int.Int.",
    >>>     "nodes": ".../nodes?filters={\"node_type\":{\"data.core.int.Int.\"}}",
    >>>     "projections": ".../nodes/projections?type=data.core.int.Int.",
    >>>     "node_schema": ".../nodes/schema?type=data.core.int.Int.",
    >>>   },
    >>>   ...
    >>> ]
    """
    api_prefix = API_CONFIG['PREFIX']
    return [
        {
            'label': model_registry.get_node_class_name(node_type),
            'node_type': node_type,
            'nodes': f'{api_prefix}/nodes?filters={{"node_type":"{node_type}"}}',
            'projections': f'{api_prefix}/nodes/projections?type={node_type}',
            'node_schema': f'{api_prefix}/nodes/schema?type={node_type}',
        }
        for node_type in sorted(
            model_registry.get_node_types(), key=lambda node_type: model_registry.get_node_class_name(node_type)
        )
    ]


@read_router.get(
    '/{uuid}',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_node(uuid: str) -> orm.Node.Model:
    """Get AiiDA node by uuid.

    :param uuid: The uuid of the node to retrieve.
    :return: The AiiDA node model, e.g. `orm.Node.Model`,
    :raises HTTPException: 422 if the node with the given uuid does not exist,
        500 for other failures during retrieval.
    """
    try:
        return service.get_one(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{uuid}/attributes',
    response_model=dict[str, t.Any],
)
@with_dbenv()
async def get_node_attributes(uuid: str) -> dict[str, t.Any]:
    """Get the attributes of a node.

    :param uuid: The uuid of the node to retrieve the attributes for.
    :return: A dictionary with the node attributes.
    :raises HTTPException: 404 if the node with the given uuid does not exist,
        500 for other failures during retrieval.
    """
    try:
        return service.get_field(uuid, 'attributes')
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{uuid}/extras',
    response_model=dict[str, t.Any],
)
@with_dbenv()
async def get_node_extras(uuid: str) -> dict[str, t.Any]:
    """Get the extras of a node.

    :param uuid: The uuid of the node to retrieve the extras for.
    :return: A dictionary with the node extras.
    :raises HTTPException: 404 if the node with the given uuid does not exist,
        500 for other failures during retrieval.
    """
    try:
        return service.get_field(uuid, 'extras')
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{uuid}/links',
    response_model=PaginatedResults[NodeLink],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_node_links(
    uuid: str,
    queries: t.Annotated[QueryParams, Depends(query_params)],
    direction: t.Literal['incoming', 'outgoing'] = Query(
        description='Specify whether to retrieve incoming or outgoing links.',
    ),
) -> PaginatedResults[NodeLink]:
    """Get the incoming or outgoing links of a node.

    :param uuid: The uuid of the node to retrieve the incoming links for.
    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :param direction: Specify whether to retrieve incoming or outgoing links.
    :return: The paginated requested linked nodes.
    :raises HTTPException: 404 if the node with the given uuid does not exist,
        500 for other failures during retrieval.
    """
    try:
        return service.get_links(uuid, queries, direction=direction)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{uuid}/download',
    response_class=StreamingResponse,
)
@with_dbenv()
async def download_node(
    uuid: str,
    download_format: str | None = Query(
        None,
        description='Format to download the node in',
    ),
) -> StreamingResponse:
    """Download AiiDA node by uuid in a given download format provided as a query parameter.

    :param uuid: The uuid of the node to retrieve.
    :param download_format: The format to download the node in.
    :return: StreamingResponse with the exported node content.
    :raises HTTPException: 403 if licensing restrictions prevent export,
        404 if the node with the given uuid does not exist,
        422 if the download format is not specified, or if the download format is not supported,
        500 for other failures during retrieval.
    """
    try:
        node = orm.load_node(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception

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
        except LicensingException as exception:
            raise HTTPException(status_code=403, detail=str(exception)) from exception

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


@read_router.get(
    '/{uuid}/repo/metadata',
    response_model=dict[str, MetadataType],
)
@with_dbenv()
async def get_node_repo_file_metadata(uuid: str) -> dict[str, dict]:
    """Get the repository file metadata of a node.

    :param uuid: The uuid of the node to retrieve the repository metadata for.
    :return: A dictionary with the repository file metadata.
    :raises HTTPException: 404 if the node with the given uuid does not exist,
        500 for other failures during retrieval.
    """
    try:
        return service.get_repository_metadata(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{uuid}/repo/contents',
    response_class=StreamingResponse,
)
@with_dbenv()
async def get_node_repo_file_contents(
    uuid: str,
    filename: str | None = Query(
        None,
        description='Filename of repository content to retrieve',
    ),
) -> StreamingResponse:
    """Get the repository contents of a node.

    :param uuid: The uuid of the node to retrieve the repository contents for.
    :param filename: The filename of the repository content to retrieve. If None, retrieves all contents.
    :return: StreamingResponse with the requested file content.
    :raises HTTPException: 404 if the node with the given uuid does not exist,
        404 if the requested file does not exist in the node's repository.
    """
    from urllib.parse import quote

    try:
        node = orm.load_node(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception

    repo = node.base.repository

    if filename:
        try:
            file_content = repo.get_object_content(filename, mode='rb')
        except FileNotFoundError as exception:
            raise HTTPException(status_code=404, detail=str(exception)) from exception

        def file_stream() -> t.Generator[bytes, None, None]:
            with io.BytesIO(file_content) as handler:
                yield from handler

        download_name = filename.split('/')[-1] or 'download'
        quoted = quote(download_name)
        headers = {'Content-Disposition': f"attachment; filename={download_name!r}; filename*=UTF-8''{quoted}"}

        return StreamingResponse(file_stream(), media_type='application/octet-stream', headers=headers)

    else:
        zip_bytes = repo.get_zipped_objects()

        def zip_stream() -> t.Generator[bytes, None, None]:
            with io.BytesIO(zip_bytes) as handler:
                yield from handler

        download_name = f'node_{uuid}_repo.zip'
        quoted = quote(download_name)
        headers = {'Content-Disposition': f"attachment; filename={download_name!r}; filename*=UTF-8''{quoted}"}

        return StreamingResponse(zip_stream(), media_type='application/zip', headers=headers)


@write_router.post(
    '',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_node(
    model: NodeModelUnion,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Create new AiiDA node.

    :param model: The AiiDA ORM model of the node to create.
    :param current_user: The current authenticated user.
    :return: The serialized created AiiDA node.
    :raises HTTPException: 422 if the node type is not recognized,
        500 for other failures during node creation.
    """
    try:
        return service.add_one(model)
    except KeyError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@write_router.post(
    '/file-upload',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_node_with_files(
    params: t.Annotated[str, Form()],
    files: list[UploadFile],
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Create new AiiDA node with files.

    :param params: The JSON string representing the AiiDA ORM model of the node to create.
    :param files: The list of uploaded files.
    :param current_user: The current authenticated user.
    :return: The serialized created AiiDA node.
    :raises HTTPException: 400 if the JSON is invalid,
        422 if the node type is not recognized,
        422 if validation of the node model fails,
        422 if any uploaded file has an invalid path or if there are duplicate target paths,
        500 for other failures during node creation.
    """
    try:
        parameters = t.cast(dict, json.loads(params))
    except json.JSONDecodeError as exception:
        raise HTTPException(400, str(exception)) from exception

    if not (node_type := parameters.get('node_type')):
        raise HTTPException(422, "Missing 'node_type' in params")

    try:
        model_cls = model_registry.get_model(node_type, which='post')
        model = model_cls(**parameters)
    except KeyError as exception:
        raise HTTPException(422, str(exception)) from exception
    except pdt.ValidationError as exception:
        raise HTTPException(422, str(exception)) from exception

    files_dict: dict[str, UploadFile] = {}

    for upload in files:
        if (target := upload.filename) in files_dict:
            raise HTTPException(422, f"Duplicate target path '{target}' in upload")
        files_dict[target] = upload

    try:
        return service.add_one(model, files=files_dict)
    except json.JSONDecodeError as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception
    except KeyError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception
