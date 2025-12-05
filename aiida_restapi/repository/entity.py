"""REST API entity repository."""

from __future__ import annotations

import typing as t

from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryParams
from aiida_restapi.common.types import EntityModelType, EntityType


class EntityRepository(t.Generic[EntityType, EntityModelType]):
    """Utility class for AiiDA REST API operations.

    This class provides methods to retrieve AiiDA entities with optional filtering, sorting, and pagination.

    :ivar entity_cls: The AiiDA ORM entity class associated with this utility, e.g. `orm.User`, `orm.Node`, etc.
    """

    def __init__(self, entity_class: type[EntityType], excluded_fields: set[str] | None = None) -> None:
        self.entity_class: type[EntityType] = entity_class
        self.excluded_fields = {'extras'} | (excluded_fields or set())

    def get_projectable_properties(self) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :return: The list of projectable properties for the AiiDA entity.
        """
        return sorted(self.entity_class.fields.keys())

    def get_entities(self, queries: QueryParams) -> PaginatedResults[EntityModelType]:
        """Get AiiDA entities with optional filtering, sorting, and/or pagination.

        :param queries: The query parameters, including filters, order_by, page_size, and page.
        :return: The paginated results, including total count, current page, page size, and list of entity models.
        """
        total = self.entity_class.collection.count(filters=queries.filters)
        results = self.entity_class.collection.find(
            filters=queries.filters,
            order_by=queries.order_by,
            limit=queries.page_size,
            offset=queries.page_size * (queries.page - 1),
        )
        return PaginatedResults[EntityModelType](
            total=total,
            page=queries.page,
            page_size=queries.page_size,
            results=[result.to_model(exclude=self.excluded_fields) for result in results],
        )

    def get_entity_by_id(self, entity_id: int) -> EntityModelType:
        """Get an AiiDA entity by id.

        :param entity_id: The id of the entity to retrieve.
        :return: The AiiDA entity model, e.g. `orm.User.Model`, `orm.Node.Model`, etc.
        """
        entity = self.entity_class.collection.get(pk=entity_id).to_model(exclude=self.excluded_fields)
        return t.cast(EntityModelType, entity)

    def create_entity(self, model: EntityModelType) -> EntityModelType:
        """Create new AiiDA entity from its model.

        :param model: The Pydantic model of the entity to create.
        :return: The created and stored AiiDA `Entity` instance.
        """
        entity = self.entity_class.from_model(model).store()
        return t.cast(EntityModelType, entity.to_model(exclude=self.excluded_fields))
