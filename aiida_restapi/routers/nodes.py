"""Declaration of FastAPI router for nodes."""

from __future__ import annotations

import io
import json
import typing as t

import pydantic as pdt
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.exceptions import ValidationException
from fastapi.responses import StreamingResponse
from typing_extensions import TypeAlias

from aiida_restapi.common import errors, query
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.config import API_CONFIG
from aiida_restapi.models.node import MetadataType, NodeLink, NodeModelRegistry, NodeStatistics, NodeType
from aiida_restapi.services.node import NodeService

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
    response_model=dict[str, t.Any],
    responses={
        422: {'model': errors.InvalidNodeTypeError},
    },
)
async def get_nodes_schema(
    node_type: t.Annotated[
        str | None,
        Query(
            description='The AiiDA node type string.',
            alias='type',
        ),
    ] = None,
    which: t.Annotated[
        t.Literal['get', 'post'],
        Query(description='Type of schema to retrieve'),
    ] = 'get',
) -> dict[str, t.Any]:
    """Get JSON schema for the base AiiDA node 'get' model."""
    if not node_type:
        return orm.Node.Model.model_json_schema()
    model = model_registry.get_model(node_type, which)
    return model.model_json_schema()


@read_router.get(
    '/projections',
    response_model=list[str],
    responses={
        422: {'model': errors.InvalidNodeTypeError},
    },
)
@with_dbenv()
async def get_node_projections(
    node_type: t.Annotated[
        str | None,
        Query(description='The AiiDA node type string.', alias='type'),
    ] = None,
) -> list[str]:
    """Get queryable projections for AiiDA nodes."""
    return service.get_projections(node_type)


@read_router.get(
    '/statistics',
    response_model=NodeStatistics,
    responses={
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_nodes_statistics(user: int | None = None) -> dict[str, t.Any]:
    """Get node statistics."""

    from aiida.manage import get_manager

    backend = get_manager().get_profile_storage()
    return backend.query().get_creation_statistics(user_pk=user)


@read_router.get('/download_formats')
async def get_nodes_download_formats() -> dict[str, t.Any]:
    """Get download formats for AiiDA nodes."""
    return service.get_download_formats()


@read_router.get(
    '',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_nodes(
    query_params: t.Annotated[
        query.QueryParams,
        Depends(query.query_params),
    ],
) -> PaginatedResults[dict[str, t.Any]]:
    """Get AiiDA nodes with optional filtering, sorting, and/or pagination."""
    return service.get_many(query_params)


@read_router.get(
    '/types',
    response_model=list[NodeType],
)
async def get_node_types() -> list:
    """Get all node types in machine-actionable format."""
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
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_node(uuid: str) -> dict[str, t.Any]:
    """Get AiiDA node by uuid."""
    return service.get_one(uuid)


@read_router.get(
    '/{uuid}/user',
    response_model=orm.User.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_node_user(uuid: str) -> dict[str, t.Any]:
    """Get the user associated with a node."""
    return service.get_related_one(uuid, orm.User)


@read_router.get(
    '/{uuid}/computer',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_node_computer(uuid: str) -> dict[str, t.Any]:
    """Get the computer associated with a node."""
    return service.get_related_one(uuid, orm.Computer)


@read_router.get(
    '/{uuid}/groups',
    response_model=PaginatedResults[orm.Group.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_node_groups(
    uuid: str,
    query_params: t.Annotated[
        query.QueryParams,
        Depends(query.query_params),
    ],
) -> PaginatedResults[dict[str, t.Any]]:
    """Get the groups of a node."""
    return service.get_related_many(uuid, orm.Group, query_params)


@read_router.get(
    '/{uuid}/attributes',
    response_model=dict[str, t.Any],
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_node_attributes(uuid: str) -> dict[str, t.Any]:
    """Get the attributes of a node."""
    return service.get_field(uuid, 'attributes')


@read_router.get(
    '/{uuid}/extras',
    response_model=dict[str, t.Any],
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_node_extras(uuid: str) -> dict[str, t.Any]:
    """Get the extras of a node."""
    return service.get_field(uuid, 'extras')


@read_router.get(
    '/{uuid}/links',
    response_model=PaginatedResults[NodeLink],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_node_links(
    uuid: str,
    direction: t.Annotated[
        t.Literal['incoming', 'outgoing'],
        Query(description='Specify whether to retrieve incoming or outgoing links.'),
    ],
    query_params: t.Annotated[
        query.QueryParams,
        Depends(query.query_params),
    ],
) -> PaginatedResults[dict[str, t.Any]]:
    """Get the incoming or outgoing links of a node."""
    return service.get_links(uuid, direction, query_params)


@read_router.get(
    '/{uuid}/repo/metadata',
    response_model=dict[str, MetadataType],
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_node_repo_file_metadata(uuid: str) -> dict[str, dict]:
    """Get the repository file metadata of a node."""
    return service.get_repository_metadata(uuid)


@read_router.get(
    '/{uuid}/repo/contents',
    response_class=StreamingResponse,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_node_repo_file_contents(
    uuid: str,
    filename: str | None = Query(
        None,
        description='Filename of repository content to retrieve',
    ),
) -> StreamingResponse:
    """Get the repository contents of a node."""
    from urllib.parse import quote

    node = orm.load_node(uuid)
    repo = node.base.repository

    if filename:
        file_content = repo.get_object_content(filename, mode='rb')

        def file_stream() -> t.Generator[bytes, None, None]:
            with io.BytesIO(file_content) as handler:
                yield from handler

        download_name = filename.split('/')[-1] or 'download'
        quoted = quote(download_name)
        headers = {'Content-Disposition': f"attachment; filename={download_name!r}; filename*=UTF-8''{quoted}"}

        return StreamingResponse(file_stream(), media_type='application/octet-stream', headers=headers)

    zip_bytes = repo.get_zipped_objects()

    def zip_stream() -> t.Generator[bytes, None, None]:
        with io.BytesIO(zip_bytes) as handler:
            yield from handler

    download_name = f'node_{uuid}_repo.zip'
    quoted = quote(download_name)
    headers = {'Content-Disposition': f"attachment; filename={download_name!r}; filename*=UTF-8''{quoted}"}

    return StreamingResponse(zip_stream(), media_type='application/zip', headers=headers)


@read_router.get(
    '/{uuid}/download',
    response_class=StreamingResponse,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.InvalidInputError},
        451: {'model': errors.InvalidLicenseError},
    },
)
@with_dbenv()
async def download_node(
    uuid: str,
    format: t.Annotated[
        str | None,
        Query(description='Format to download the node in'),
    ] = None,
) -> StreamingResponse:
    """Download AiiDA node by uuid in a given download format provided as a query parameter."""
    node = orm.load_node(uuid)

    if format is None:
        raise ValidationException(
            'Please specify the download format. '
            'The available download formats can be '
            'queried using the /nodes/download_formats/ endpoint.',
        )

    if format in node.get_export_formats():
        # byteobj, dict with {filename: filecontent}
        exported_bytes, _ = node._exportcontent(format)

        def stream() -> t.Generator[bytes, None, None]:
            with io.BytesIO(exported_bytes) as handler:
                yield from handler

        return StreamingResponse(stream(), media_type=f'application/{format}')

    raise ValidationException(
        'The format {} is not supported. '
        'The available download formats can be '
        'queried using the /nodes/download_formats/ endpoint.'.format(format),
    )


@write_router.post(
    '',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        403: {'model': errors.StoringNotAllowedError},
        422: {'model': t.Union[errors.RequestValidationError, errors.InvalidInputError, errors.InvalidNodeTypeError]},
    },
)
@with_dbenv()
async def create_node(
    model: NodeModelUnion,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> dict[str, t.Any]:
    """Create new AiiDA node."""
    return service.add_one(model)


@write_router.post(
    '/file-upload',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        400: {'model': errors.JsonDecodingError},
        403: {'model': errors.StoringNotAllowedError},
        422: {'model': t.Union[errors.RequestValidationError, errors.InvalidInputError, errors.InvalidNodeTypeError]},
    },
)
@with_dbenv()
async def create_node_with_files(
    params: t.Annotated[str, Form()],
    files: list[UploadFile],
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> dict[str, t.Any]:
    """Create new AiiDA node with files."""
    parameters = t.cast(dict, json.loads(params))

    if not (node_type := parameters.get('node_type')):
        raise ValidationException("The 'node_type' field is missing in the parameters.")

    model_cls = model_registry.get_model(node_type, which='post')
    model = model_cls(**parameters)

    files_dict: dict[str, UploadFile] = {}

    for upload in files:
        if (target := upload.filename) in files_dict:
            raise ValidationException(f"Duplicate target path '{target}' in upload")
        files_dict[target] = upload

    return service.add_one(model, files=files_dict)
