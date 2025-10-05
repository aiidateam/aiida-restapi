"""REST API utilities."""

from __future__ import annotations

import typing as t
from pathlib import Path

from aiida import orm
from fastapi import HTTPException

from .pagination import PaginatedResults
from .query import QueryParams
from .types import EntityModelType, EntityType, NodeModelType, NodeType


class EntityRepository(t.Generic[EntityType, EntityModelType]):
    """Utility class for AiiDA REST API operations.

    This class provides methods to retrieve AiiDA entities with optional filtering, sorting, and pagination.

    :ivar entity_cls: The AiiDA ORM entity class associated with this utility, e.g. `orm.User`, `orm.Node`, etc.
    """

    def __init__(self, orm_entity: type[EntityType]):
        self.entity_cls: type[EntityType] = orm_entity

    def get_projectable_properties(self) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :return: The list of projectable properties for the AiiDA entity.
        """
        return sorted(self.entity_cls.fields.keys())

    def get_entities(self, queries: QueryParams) -> PaginatedResults[EntityModelType]:
        """Get AiiDA entities with optional filtering, sorting, and/or pagination.

        :param queries: The query parameters, including filters, order_by, page_size, and page.
        :return: The paginated results, including total count, current page, page size, and list of entity models.
        """
        total = self.entity_cls.collection.count(filters=queries.filters)
        results = self.entity_cls.collection.find(
            filters=queries.filters,
            order_by=queries.order_by,
            limit=queries.page_size,
            offset=queries.page_size * (queries.page - 1),
        )
        return PaginatedResults[EntityModelType](
            total=total,
            page=queries.page,
            page_size=queries.page_size,
            results=[result.to_model() for result in results],
        )

    def get_entity_by_id(self, entity_id: int) -> EntityModelType:
        """Get an AiiDA entity by id.

        :param entity_id: The id of the entity to retrieve.
        :return: The AiiDA entity model, e.g. `orm.User.Model`, `orm.Node.Model`, etc.
        :raises HTTPException: If the entity with the given id does not exist.
        """
        try:
            return t.cast(
                EntityModelType,
                self.entity_cls.collection.get(pk=entity_id).to_model(),
            )
        except Exception:
            raise HTTPException(
                status_code=404,
                detail=f'Could not find any {self.entity_cls.__name__.lower()} with id {entity_id}',
            )

    def create_entity(self, model: EntityModelType) -> EntityModelType:
        """Create new AiiDA entity from its model.

        :param model: The Pydantic model of the entity to create.
        :return: The created and stored AiiDA `Entity` instance.
        """
        entity = self.entity_cls.from_model(model).store()
        return t.cast(EntityModelType, entity.to_model())


class NodeRepository(EntityRepository[NodeType, NodeModelType]):
    """Utility class for AiiDA Node REST API operations."""

    def get_projectable_properties(self, node_type: str | None = None) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :param node_type: The node type name of the AiiDA entity.
        :return: The list of projectable properties for the AiiDA entity.
        :raises HTTPException: If the node type is unknown.
        """
        if not node_type:
            return super().get_projectable_properties()
        else:
            try:
                node_cls = orm.utils.load_node_class(node_type)
                return sorted(node_cls.fields.keys())
            except KeyError:
                raise HTTPException(status_code=404, detail='Unknown node type')

    def create_entity(self, model: NodeModelType) -> NodeModelType:
        """Create new AiiDA node from its model.

        :param node_model: The Pydantic model of the node to create.
        :return: The created and stored AiiDA `Node` instance.
        """
        node_cls = orm.utils.load_node_class(model.node_type)
        node = node_cls.from_model(model)
        node.base.attributes.set_many(model.attributes or {})
        node.base.extras.set_many(model.extras or {})
        node.base.repository.repository_metadata = model.repository_metadata
        node.store()
        return t.cast(NodeModelType, node.to_model())

    def create_node_with_file(
        self,
        node_cls: type[NodeType],
        node_dict: dict,
        file: Path,
    ) -> NodeModelType:
        """Create and store `Node` with file.

        :param node_cls: The AiiDA ORM Node class to instantiate.
        :param node_dict: The dictionary of node attributes, extras, and repository metadata.
        :param file: The file to be uploaded to the node's repository.
        :return: The created and stored AiiDA Node instance.
        """
        attributes = node_dict.pop('attributes', {})
        extras = node_dict.pop('extras', {})
        node = node_cls(file=file, **node_dict, **attributes)
        node.base.extras.set_many(extras)
        node.store()
        return t.cast(NodeModelType, node.to_model())
