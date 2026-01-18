from __future__ import annotations

import typing as t

from aiida import orm
from aiida.common.exceptions import NotExistent

from .utils import IncludedItemParamsCache

IncludedItemParams = tuple[t.Union[str, int], str, dict[str, t.Any], dict[str, t.Any]]
# (id, type, attributes, foreign fields)


class BaseHook:
    """The base hook for JSON:API document customization."""

    TYPE_MAP: dict[str, str] = {}

    FOREIGN_FIELDS: list[str] = []

    INCLUDED_TYPE_MAP: dict[str, tuple[str, type[orm.Entity]]] = {}

    @classmethod
    def split_resource(
        cls,
        result: dict[str, t.Any],
        resource_identity: str,
        resource_type: str,
    ) -> tuple[str, dict[str, t.Any], dict[str, t.Any]]:
        """Split the result into identifier, attributes, and foreign fields.

        :param result: The raw result of the resource.
        :type result: dict[str, t.Any]
        :param resource_identity: The identity field of the resource.
        :type resource_identity: str
        :param resource_type: The type of the resource.
        :type resource_type: str
        :return: A tuple containing the identifier, attributes, and foreign fields.
        :rtype: tuple[str, dict[str, t.Any], dict[str, t.Any]]
        """
        if not (identifier := str(result.get(resource_identity, ''))):
            raise ValueError(f"Missing '{resource_identity}' in model dump for resource_type={resource_type!r}")
        attributes: dict[str, t.Any] = {}
        foreign_fields: dict[str, t.Any] = {}
        for key, value in result.items():
            if key in cls.FOREIGN_FIELDS:
                foreign_fields[key] = value
            elif key != resource_identity:
                attributes[key] = value
        return identifier, attributes, foreign_fields

    @classmethod
    def links(
        cls,
        *,
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, str | dict[str, t.Any]]:
        """Return link dictionary for the resource.

        :param resource_type: The type of the resource.
        :type resource_type: str
        :param base_api_url: The base URL of the API.
        :type base_api_url: str
        :param url_id: The URL identifier of the resource.
        :type url_id: str
        :return: A dictionary of links.
        :rtype: dict[str, str | dict[str, t.Any]]
        """
        return {}

    @classmethod
    def relationships(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, dict[str, t.Any]]:
        """Return relationships dictionary for the resource.

        :param foreign_fields: The foreign fields of the resource.
        :type foreign_fields: dict[str, t.Any]
        :param resource_type: The type of the resource.
        :type resource_type: str
        :param base_api_url: The base URL of the API.
        :type base_api_url: str
        :param url_id: The URL identifier of the resource.
        :type url_id: str
        :return: A dictionary of relationships.
        :rtype: dict[str, dict[str, t.Any]]
        """
        return {}

    @classmethod
    def include(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        include: list[str],
        cache: IncludedItemParamsCache | None = None,
    ) -> list[IncludedItemParams]:
        included: list[IncludedItemParams] = []

        for item in include:
            if item not in cls.FOREIGN_FIELDS:
                raise NotExistent(f"Include field '{item}' not recognized; valid fields: {cls.FOREIGN_FIELDS}")
            if not (identifier := foreign_fields.get(item, None)):
                continue
            if included_item := cls._build_included_item(
                identifier,
                *cls.INCLUDED_TYPE_MAP[item],
                cache=cache,
            ):
                included.append(included_item)

        return included

    @classmethod
    def _build_included_item(
        cls,
        resource_id: str | int,
        resource_type: str,
        orm_class: type[orm.Entity],
        cache: IncludedItemParamsCache | None = None,
    ) -> IncludedItemParams | None:
        """Build an included item parameters tuple.

        :param resource_id: The identifier of the resource.
        :type resource_id: str | int
        :param resource_type: The type of the resource.
        :type resource_type: str
        :param orm_class: The ORM class of the resource.
        :type orm_class: type[orm.Entity]
        :param cache: An optional cache for included resources.
        :type cache: IncludedItemParamsCache | None
        :return: A tuple containing identifier, type, attributes, and foreign fields of the included resource,
            or None if resource_id is None.
        :rtype: IncludedItemParams | None
        """
        if resource_id is None:
            return None

        bucket = cache.bucket(resource_type) if cache is not None else None

        cache_key = str(resource_id)

        if bucket is not None and cache_key in bucket:
            return None

        node: orm.Entity = orm_class.collection.get(**{orm_class.identity_field: resource_id})
        node_dict = node.serialize(minimal=True)
        identifier, attributes, foreign_fields = cls.split_resource(
            node_dict,
            node.identity_field,
            resource_type,
        )
        included_item: IncludedItemParams = (identifier, resource_type, attributes, foreign_fields)

        if bucket is not None:
            bucket[cache_key] = included_item

        return included_item


class ResourceHook(BaseHook):
    """A hook for JSON:API resource customization."""

    @classmethod
    def links(
        cls,
        *,
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, str | dict[str, t.Any]]:
        return {
            'self': f'{base_api_url}/{resource_type}/{url_id}',
        }

    @classmethod
    def relationships(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, dict[str, t.Any]]:
        return {
            'collection': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}',
                }
            }
        }


class EntityHook(ResourceHook):
    """A hook for entity-specific JSON:API customization."""

    TYPE_MAP: dict[str, str] = {
        'users': 'user',
        'computers': 'computer',
        'nodes': 'node',
        'groups': 'group',
    }

    INCLUDED_TYPE_MAP: dict[str, tuple[str, type[orm.Entity]]] = {
        'user': ('users', orm.User),
        'computer': ('computers', orm.Computer),
        'node': ('nodes', orm.Node),
        'group': ('groups', orm.Group),
    }


class ComputerHook(EntityHook):
    """A hook for computer-specific JSON:API customization."""

    @classmethod
    def relationships(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, dict[str, t.Any]]:
        extra = {
            'metadata': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/metadata',
                }
            },
        }
        return (
            super().relationships(
                foreign_fields=foreign_fields,
                resource_type=resource_type,
                base_api_url=base_api_url,
                url_id=url_id,
            )
            | extra
        )


class GroupHook(EntityHook):
    """A hook for group-specific JSON:API customization."""

    FOREIGN_FIELDS: list[str] = ['user']

    @classmethod
    def relationships(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, dict[str, t.Any]]:
        extra = {
            'user': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/user',
                },
                'data': {
                    'id': str(foreign_fields.get('user')),
                    'type': 'users',
                },
            },
            'nodes': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/nodes',
                }
            },
            'extras': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/extras',
                }
            },
        }
        return (
            super().relationships(
                foreign_fields=foreign_fields,
                resource_type=resource_type,
                base_api_url=base_api_url,
                url_id=url_id,
            )
            | extra
        )


class NodeHook(EntityHook):
    """A hook for node-specific JSON:API customization."""

    FOREIGN_FIELDS: list[str] = ['user', 'computer']

    @classmethod
    def relationships(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, dict[str, t.Any]]:
        extra = {
            'user': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/user',
                },
                'data': {
                    'id': str(foreign_fields.get('user')),
                    'type': 'users',
                },
            },
        }

        # Not all nodes have an associated computer
        computer_id = foreign_fields.get('computer', None)
        if computer_id is not None:
            extra['computer'] = {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/computer',
                },
                'data': {
                    'id': str(computer_id),
                    'type': 'computers',
                },
            }

        extra |= {
            'groups': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/groups',
                }
            },
            'attributes': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/attributes',
                }
            },
            'extras': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/extras',
                }
            },
            'repository_metadata': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/repo/metadata',
                }
            },
            'incoming': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/links?direction=incoming',
                }
            },
            'outgoing': {
                'links': {
                    'related': f'{base_api_url}/{resource_type}/{url_id}/links?direction=outgoing',
                }
            },
        }

        return (
            super().relationships(
                foreign_fields=foreign_fields,
                resource_type=resource_type,
                base_api_url=base_api_url,
                url_id=url_id,
            )
            | extra
        )


class LinkHook(BaseHook):
    """A hook for link-specific JSON:API customization."""

    FOREIGN_FIELDS: list[str] = ['source', 'target']

    INCLUDED_TYPE_MAP: dict[str, tuple[str, type[orm.Entity]]] = {
        'source': ('nodes', orm.Node),
        'target': ('nodes', orm.Node),
    }

    @classmethod
    def relationships(
        cls,
        *,
        foreign_fields: dict[str, t.Any],
        resource_type: str,
        base_api_url: str,
        url_id: str,
    ) -> dict[str, dict[str, t.Any]]:
        extra = {}
        if source := foreign_fields.get('source', None):
            extra['source'] = {
                'links': {
                    'related': f'{base_api_url}/nodes/{source}',
                },
                'data': {
                    'id': str(source),
                    'type': 'nodes',
                },
            }
        if target := foreign_fields.get('target', None):
            extra['target'] = {
                'links': {
                    'related': f'{base_api_url}/nodes/{target}',
                },
                'data': {
                    'id': str(target),
                    'type': 'nodes',
                },
            }
        return extra
