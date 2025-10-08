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

from .auth import get_current_active_user

router = APIRouter()


repository = NodeRepository[orm.Node, orm.Node.Model](orm.Node)
model_registry = NodeModelRegistry()


@router.get('/nodes/schema')
async def get_nodes_schema() -> dict[str, dict[str, t.Any]]:
    """Get JSON schema for AiiDA nodes.

    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    """
    return {
        'get': orm.Node.Model.model_json_schema(),
        'post': {model.__name__: model.model_json_schema() for model in model_registry.get_models()},
    }


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
async def get_nodes_types() -> list[str]:
    """Get available AiiDA node class names.

    :return: List of available AiiDA node class names.
    """
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
    """Get AiiDA nodes by node type with optional filtering, sorting, and/or pagination.

    :param node_class: The name of the AiiDA node class.
    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of node models.
    :raises HTTPException: If the node class is not recognized (404), or on failure (400).
    """
    try:
        node_type = model_registry.get_node_type(node_class)
        queries.filters['node_type'] = {'like': f'%{node_type}%'}
        return repository.get_entities(queries)
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


@router.get('/nodes/types/{node_class}/projectable_properties')
@with_dbenv()
async def get_node_class_projectable_properties(node_class: str) -> list[str]:
    """Get projectable properties of a given AiiDA node class.

    :param node_class: The name of the AiiDA node class.
    :return: The list of projectable properties for the given AiiDA node class.
    :raises HTTPException: If the node class is not recognized (404), or on failure (400).
    """
    try:
        node_type = model_registry.get_node_type(node_class)
        return repository.get_projectable_properties(node_type)
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


@router.get('/nodes/types/{node_class}/schema')
async def get_node_class_schema(node_class: str) -> dict[str, t.Any]:
    """Get JSON schema for a given AiiDA node class.

    :param node_class: The name of the AiiDA node class.
    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    :raises HTTPException: If the node class is not recognized (404), or on failure (400).
    """
    try:
        NodeModel = model_registry.get_model(node_class)
        return {
            'get': orm.Node.Model.model_json_schema(),
            'post': NodeModel.model_json_schema(),
        }
    except KeyError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception


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
    """Create new AiiDA node.

    :param node_model: The AiiDA ORM model of the node to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA node.
    :raises HTTPException: If the node class is not recognized (404),
        or if creation fails (400).
    """
    try:
        node_type = model_registry.get_node_type(node_model.orm_class)
        return repository.create_entity(node_model, node_type)
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
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
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
        node_class = params_dict.get('orm_class', 'SinglefileData')
        node_model = model_registry.get_model(node_class)
        model = node_model(**params_dict)
        node_type = model_registry.get_node_type(node_class)
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
    return repository.create_entity(model, node_type)
