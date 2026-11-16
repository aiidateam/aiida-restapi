"""JSON:API adapters module."""

from __future__ import annotations

import typing as t
from urllib.parse import urlencode

from aiida import orm
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
        resource, included = cls._build_resource(
            request,
            result,
            resource_identity,
            resource_type,
            include,
        )

        return {
            'links': {
                'self': cls._build_link(request),
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
        hook = cls._hook_for(parent_type)

        included = (
            [
                cls._to_resource(
                    request,
                    included_identifier,
                    included_attributes,
                    included_foreign_fields,
                    included_type,
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
            request,
            result,
            pid,
            parent_type,
            child_type,
        )

        return {
            'links': {
                'self': cls._build_link(request),
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

        resources: list[dict[str, t.Any]] = []
        included: list[dict[str, t.Any]] = []

        included_cache = IncludedItemParamsCache()

        for result in results.data:
            resource, included_items = cls._build_resource(
                request,
                result,
                resource_identity,
                resource_type,
                query_params.include,
                included_cache,
            )
            resources.append(resource)
            included.extend(included_items)

        meta = {
            'total': results.total,
            'offset': results.offset,
            'limit': results.limit,
        } | (meta or {})

        toplevel_links = cls._build_toplevel_links(
            request,
            results.total,
            query_params.offset,
            query_params.limit,
            query_params.query_items,
        )

        return {
            'links': toplevel_links,
            'meta': meta,
            'included': included or None,
            'data': resources,
        }

    @classmethod
    def _build_resource(
        cls,
        request: Request,
        result: dict[str, t.Any],
        resource_identity: str,
        resource_type: str,
        include: list[str] | None = None,
        cache: IncludedItemParamsCache | None = None,
    ) -> tuple[dict[str, t.Any], list[dict[str, t.Any]]]:
        """Build a JSON:API resource and its included related resources.

        :param request: The incoming request.
        :type request: Request
        :param result: The result to convert.
        :type result: dict[str, t.Any]
        :param resource_identity: The identity field to use for the resource.
        :type resource_identity: str
        :param resource_type: The resource type to use for the resource.
        :type resource_type: str
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
                    request,
                    included_identifier,
                    included_attributes,
                    included_foreign_fields,
                    included_type,
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
            request,
            identifier,
            attributes,
            foreign_fields,
            resource_type,
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
        request: Request,
        identifier: str | int,
        attributes: dict[str, t.Any],
        foreign_fields: dict[str, t.Any],
        resource_type: str,
    ) -> dict[str, t.Any]:
        """Convert an AiiDA quantity to a JSON:API resource.

        :param request: The incoming request.
        :type request: Request
        :param resource_identity: The identity field to use for the resource.
        :type resource_identity: str
        :param resource_type: The resource type to use for the resource.
        :type resource_type: str
        :return: The JSON:API resource object.
        :rtype: dict[str, t.Any]
        """
        hook = cls._hook_for(resource_type)

        links = hook.links(
            request,
            resource_type=resource_type,
            url_id=str(identifier),
        )

        relationships = hook.relationships(
            request,
            foreign_fields=foreign_fields,
            resource_type=resource_type,
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
        request: Request,
        result: dict[str, t.Any],
        pid: str | int,
        parent_type: str,
        child_type: str,
    ) -> dict[str, t.Any]:
        """Convert a dependent quantity to a single resource JSON:API document.

        :param request: The incoming request.
        :type request: Request
        :param result: The result dictionary to convert.
        :type result: dict[str, t.Any]
        :param pid: The parent resource identifier.
        :type pid: str | int
        :param parent_type: The parent resource type.
        :type parent_type: str
        :param child_type: The child resource type.
        :type child_type: str
        :return: The JSON:API resource object.
        :rtype: dict[str, t.Any]
        """
        root = f'{request.scope["root_path"]}{API_CONFIG["PREFIX"]}/{parent_type}'

        pid = str(pid)  # ensure pid is a string for URL construction

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
                        'id': pid,
                        'type': parent_type,
                    },
                }
            },
        }

    @classmethod
    def _build_toplevel_links(
        cls,
        request: Request,
        total: int,
        offset: int,
        limit: int,
        query_items: list[tuple[str, str]],
    ) -> dict[str, str]:
        """Return dict suitable for JSON:API top-level links (self/next/prev/first/last).

        :param request: The incoming request.
        :type request: Request
        :param total: The total number of items.
        :type total: int
        :param offset: The number of results skipped.
        :type offset: int
        :param limit: The maximum number of results returned.
        :type limit: int
        :param query_items: The query parameters to include in the links.
        :type query_items: list[tuple[str, str]]
        :return: The top-level links.
        :rtype: dict[str, str]
        """
        links = {
            'self': cls._build_link(request, query_items, offset=offset, limit=limit),
            'first': cls._build_link(request, query_items, offset=0, limit=limit),
            'last': cls._build_link(request, query_items, offset=max(0, ((total - 1) // limit) * limit), limit=limit),
        }

        if offset > 0:
            links['prev'] = cls._build_link(request, query_items, offset=max(0, offset - limit), limit=limit)
        if offset + limit < total:
            links['next'] = cls._build_link(request, query_items, offset=offset + limit, limit=limit)

        return links

    @staticmethod
    def _build_link(
        request: Request,
        query_items: list[tuple[str, str]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> str:
        """Return a relative URL with updated query parameters.

        :param request: The incoming request.
        :type request: Request
        :param query_items: The query parameters to include in the link.
        :type query_items: list[tuple[str, str]] | None
        :param offset: The number of results skipped.
        :type offset: int | None
        :param limit: The maximum number of results returned.
        :type limit: int | None
        :return: The updated URL relative to the base URL.
        :rtype: str
        """
        source_query_items = request.query_params.multi_items() if query_items is None else query_items
        query = [(key, value) for key, value in source_query_items if key not in {'page[offset]', 'page[limit]'}]
        if offset is not None:
            query.append(('page[offset]', str(offset)))
        if limit is not None:
            query.append(('page[limit]', str(limit)))

        link = request.url.path
        safe_key_chars = r'[]<>=!'
        safe_value_chars = r'%[]{}:!,?@&=+$-_.~*\'()"'
        if query:
            link += f'?{urlencode(query, safe=safe_key_chars + safe_value_chars)}'

        return link
