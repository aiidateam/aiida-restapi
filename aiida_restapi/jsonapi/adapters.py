"""JSON:API adapters module."""

from __future__ import annotations

import typing as t

from aiida import orm
from fastapi.datastructures import URL
from starlette.requests import Request

from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import CollectionQueryParams
from aiida_restapi.config import API_CONFIG

from . import hooks
from .utils import IncludedItemParamsCache


class JsonApiAdapter:
    """JSON:API adapter to convert AiiDA models to JSON:API compliant documents."""

    RESOURCE_TYPES: dict[type[orm.Entity], str] = {
        orm.User: 'users',
        orm.Computer: 'computers',
        orm.Group: 'groups',
        orm.Node: 'nodes',
    }

    HOOKS: dict[str, type[hooks.BaseHook]] = {
        'users': hooks.ResourceHook,
        'computers': hooks.ComputerHook,
        'groups': hooks.GroupHook,
        'nodes': hooks.NodeHook,
        'links': hooks.LinkHook,
    }

    BASE_API_URL = ''

    @classmethod
    def register_hooks(cls, new_hooks: dict[str, type[hooks.BaseHook]]) -> None:
        """Update the hook mapping with new hooks.

        :param new_hooks: A dictionary of resource type to Hook class mappings.
        :type new_hooks: dict[str, type[Hook]]
        """
        cls.HOOKS.update(new_hooks)

    @classmethod
    def resource(
        cls,
        request: Request,
        result: dict[str, t.Any],
        *,
        resource_identity: str,
        resource_type: str,
        include: list[str] | None = None,
        meta: dict[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Return a JSON:API document for a single resource derived from an AiiDA object.

        :param request: The incoming request.
        :type request: Request
        :param result: The result model to convert.
        :type result: dict[str, t.Any]
        :param resource_identity: The identity field to use for the resource.
        :type resource_identity: str
        :param resource_type: The resource type to use for the resource.
        :type resource_type: str
        :param include: A list of related resource types to include.
        :type include: list[str] | None
        :param meta: Optional meta information to include in the document.
        :type meta: dict[str, t.Any] | None
        :return: The JSON:API document.
        :rtype: JsonApiResponse
        """
        base_api = cls._base_api_url(request)

        resource, included = cls._build_resource(
            result,
            resource_identity,
            resource_type,
            base_api,
            include=include,
        )

        return {
            'links': {
                'self': str(request.url),
            },
            'data': resource,
            'included': included or None,
            'meta': meta,
        }

    @classmethod
    def child_resource(
        cls,
        request: Request,
        result: dict[str, t.Any],
        *,
        pid: str | int,
        parent_type: str,
        child_type: str,
        include: list[str] | None = None,
        meta: dict[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Return a JSON:API document for a child resource derived from an AiiDA object's child quantity.

        :param request: The incoming request.
        :type request: Request
        :param result: The result dictionary to convert.
        :type result: dict[str, t.Any]
        :param pid: The parent resource identifier.
        :type pid: str | int
        :param child_type: The child resource type.
        :type child_type: str
        :param parent_type: The parent resource type.
        :type parent_type: str | None
        :param include: A list of related resource types to include.
        :type include: list[str] | None
        :param meta: Optional meta information to include in the document.
        :type meta: dict[str, t.Any] | None
        :return: The JSON:API document.
        :rtype: JsonApiResponse
        """
        base_api = cls._base_api_url(request)

        hook = cls._hook_for(parent_type)

        included = (
            [
                cls._to_resource(
                    included_identifier,
                    included_attributes,
                    included_foreign_fields,
                    included_type,
                    base_api,
                )
                for (
                    included_identifier,
                    included_type,
                    included_attributes,
                    included_foreign_fields,
                ) in hook.include(
                    foreign_fields={hook.TYPE_MAP[parent_type]: pid},
                    include=include,
                )
            ]
            if include
            else []
        )

        child_resource = cls._to_child_resource(
            result,
            pid=pid,
            parent_type=parent_type,
            child_type=child_type,
            base_api=base_api,
        )

        return {
            'links': {
                'self': str(request.url),
            },
            'data': child_resource,
            'included': included or None,
            'meta': meta,
        }

    @classmethod
    def collection(
        cls,
        request: Request,
        results: PaginatedResults,
        *,
        resource_identity: str,
        resource_type: str,
        query_params: CollectionQueryParams = CollectionQueryParams(),
        meta: dict[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Return a JSON:API document with a collection of resources derived from AiiDA objects.

        :param request: The incoming request.
        :type request: Request
        :param results: The paginated results to convert.
        :type results: PaginatedResults
        :param resource_identity: The identity field to use for the resources.
        :type resource_identity: str
        :param resource_type: The resource type to use for the resources.
        :type resource_type: str
        :param query_params: The collection query parameters.
        :type query_params: CollectionQueryParams
        :param meta: Optional meta information to include in the document.
        :type meta: dict[str, t.Any] | None
        :return: The JSON:API document.
        :rtype: JsonApiResponse
        """

        base_api = cls._base_api_url(request)

        resources: list[dict[str, t.Any]] = []
        included: list[dict[str, t.Any]] = []

        included_cache = IncludedItemParamsCache()

        for result in results.data:
            resource, included_items = cls._build_resource(
                result,
                resource_identity,
                resource_type,
                base_api,
                include=query_params.include,
                cache=included_cache,
            )
            resources.append(resource)
            included.extend(included_items)

        pagination = {
            'total': results.total,
            'page': query_params.page,
            'page_size': query_params.page_size,
        } | (meta or {})

        toplevel_links = cls._build_toplevel_links(request, **pagination)

        return {
            'links': toplevel_links,
            'meta': pagination,
            'included': included or None,
            'data': resources,
        }

    @classmethod
    def _base_api_url(cls, request: Request) -> str:
        """Return the base API URL from the request.

        :param request: The incoming request.
        :type request: Request
        :return: The base API URL.
        :rtype: str
        """
        if not cls.BASE_API_URL:
            base = str(request.base_url).rstrip('/')
            cls.BASE_API_URL = f'{base}/{API_CONFIG["PREFIX"].lstrip("/")}'
        return cls.BASE_API_URL

    @classmethod
    def _build_resource(
        cls,
        result: dict[str, t.Any],
        resource_identity: str,
        resource_type: str,
        base_api: str,
        include: list[str] | None = None,
        cache: IncludedItemParamsCache | None = None,
    ) -> tuple[dict[str, t.Any], list[dict[str, t.Any]]]:
        """Build a JSON:API resource and its included related resources.
        :param result: The result to convert.
        :type result: dict[str, t.Any]
        :param resource_identity: The identity field to use for the resource.
        :type resource_identity: str
        :param resource_type: The resource type to use for the resource.
        :type resource_type: str
        :param base_api: The base API URL.
        :type base_api: str
        :param include: A list of related resource types to include.
        :type include: list[str] | None
        :param cache: An optional cache for included resources.
        :type cache: IncludedItemParamsCache | None
        :return: The JSON:API resource and included resources.
        :rtype: tuple[dict[str, t.Any], list[dict[str, t.Any]]]
        :raises JsonApiException: If the resource identity or type are missing.
        """
        hook = cls._hook_for(resource_type)

        identifier, attributes, foreign_fields = hook.split_resource(
            result,
            resource_identity,
            resource_type,
        )

        included = (
            [
                cls._to_resource(
                    included_identifier,
                    included_attributes,
                    included_foreign_fields,
                    included_type,
                    base_api,
                )
                for (
                    included_identifier,
                    included_type,
                    included_attributes,
                    included_foreign_fields,
                ) in hook.include(
                    foreign_fields=foreign_fields,
                    include=include,
                    cache=cache,
                )
            ]
            if include
            else []
        )

        resource = cls._to_resource(
            identifier,
            attributes,
            foreign_fields,
            resource_type,
            base_api,
        )

        return resource, included

    @classmethod
    def _hook_for(cls, resource_type: str) -> type[hooks.BaseHook]:
        """Return the Hook class for the given resource type.

        :param resource_type: The resource type.
        :type resource_type: str
        :return: The hook class.
        :rtype: type[Hook]
        """
        return cls.HOOKS.get(resource_type, hooks.BaseHook)

    @classmethod
    def _to_resource(
        cls,
        identifier: str | int,
        attributes: dict[str, t.Any],
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api: str,
    ) -> dict[str, t.Any]:
        """Convert an AiiDA quantity to a JSON:API resource.

        :param result: The result dictionary to convert.
        :type result: dict[str, t.Any]
        :param base_api: The base API URL.
        :type base_api: str
        :param resource_identity: The identity field to use for the resource.
        :type resource_identity: str
        :param resource_type: The resource type to use for the resource.
        :type resource_type: str
        :return: The JSON:API resource object.
        :rtype: dict[str, t.Any]
        """
        hook = cls._hook_for(resource_type)

        links = hook.links(
            resource_type=resource_type,
            base_api_url=base_api,
            url_id=str(identifier),
        )

        relationships = hook.relationships(
            foreign_fields=foreign_fields,
            resource_type=resource_type,
            base_api_url=base_api,
            url_id=str(identifier),
        )

        return {
            'id': identifier,
            'type': resource_type,
            'links': links or None,
            'attributes': attributes or None,
            'relationships': relationships or None,
        }

    @classmethod
    def _to_child_resource(
        cls,
        result: dict[str, t.Any],
        *,
        pid: str | int,
        parent_type: str,
        child_type: str,
        base_api: str,
    ) -> dict[str, t.Any]:
        """Convert an dependent quantity to a single resource JSON:API document.

        :param result: The result dictionary to convert.
        :type result: dict[str, t.Any]
        :param pid: The parent resource identifier.
        :type pid: str | int
        :param parent_type: The parent resource type.
        :type parent_type: str
        :param child_type: The child resource type.
        :type child_type: str
        :param base_api: The base API URL.
        :type base_api: str
        :return: The JSON:API resource object.
        :rtype: dict[str, t.Any]
        """
        root = f'{base_api}/{parent_type}'

        return {
            'id': pid,
            'type': child_type,
            'links': {
                'self': f'{root}/{pid}/{child_type.replace("-", "/")}',
            },
            'attributes': result,
            'relationships': {
                'parent': {
                    'links': {
                        'related': f'{root}/{pid}',
                    },
                    'data': {
                        'id': str(pid),
                        'type': parent_type,
                    },
                }
            },
        }

    @classmethod
    def _build_toplevel_links(
        cls,
        request: Request,
        page_size: int,
        page: int,
        total: int,
    ) -> dict[str, str]:
        """Return dict suitable for JSON:API top-level links (self/next/prev/first/last).

        :param request: The incoming request.
        :type request: Request
        :param page_size: The page size.
        :type page_size: int
        :param page: The current page.
        :type page: int
        :param total: The total number of items.
        :type total: int
        :return: The top-level links.
        :rtype: dict[str, str]
        """
        current = cls._build_link(request, page=page, page_size=page_size)

        links: dict[str, str] = {'self': str(current)}

        if page > 1:
            links['prev'] = str(cls._build_link(request, page=page - 1, page_size=page_size))
            links['first'] = str(cls._build_link(request, page=1, page_size=page_size))

        last_page = (total + page_size - 1) // page_size if page_size > 0 else 1
        if last_page >= 1:
            links['last'] = str(cls._build_link(request, page=last_page, page_size=page_size))

        if page < last_page:
            links['next'] = str(cls._build_link(request, page=page + 1, page_size=page_size))

        return links

    @staticmethod
    def _build_link(request: Request, **updates: str | int | None) -> URL:
        """Return a URL with updated query parameters.

        :param request: The incoming request.
        :type request: Request
        :param updates: The query parameter updates.
        :type updates: dict[str, str | int | None]
        :return: The updated URL.
        :rtype: URL
        """
        url = request.url
        q = dict(request.query_params)

        for k, v in updates.items():
            if v is None:
                q.pop(k, None)
            else:
                q[k] = str(v)

        return url.replace_query_params(**q)
