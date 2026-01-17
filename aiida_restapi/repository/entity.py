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

    def __init__(self, entity_class: type[EntityType]) -> None:
        self.entity_class: type[EntityType] = entity_class

    def get_entity_schema(self, which: t.Literal['get', 'post'] | None = None) -> dict:
        """Get JSON schema for the AiiDA entity.

        :param which: The type of schema to retrieve: 'get' or 'post'.
        :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
        :raises ValueError: If the 'which' parameter is not 'get' or 'post'.
        """
        if not which:
            return {
                'get': self.entity_class.Model.model_json_schema(),
                'post': self.entity_class.CreateModel.model_json_schema(),
            }
        elif which == 'get':
            return self.entity_class.Model.model_json_schema()
        elif which == 'post':
            return self.entity_class.CreateModel.model_json_schema()
        raise ValueError(f'Schema type "{which}" not supported; expected "get" or "post"')

    def get_projectable_properties(self) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :return: The list of projectable properties for the AiiDA entity.
        """
        return self.entity_class.fields.keys()

    def get_entities(self, queries: QueryParams) -> PaginatedResults:
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
        return PaginatedResults(
            total=total,
            page=queries.page,
            page_size=queries.page_size,
            results=[self.to_model(result) for result in results],
        )

    def get_entity_by_id(self, entity_id: int) -> EntityModelType:
        """Get an AiiDA entity by id.

        :param entity_id: The id of the entity to retrieve.
        :return: The AiiDA entity model, e.g. `orm.User.Model`, `orm.Node.Model`, etc.
        """
        entity = self.entity_class.collection.get(pk=entity_id)
        return self.to_model(entity)

    def get_entity_extras(self, entity_id: int) -> dict[str, t.Any]:
        """Get the extras of an entity.

        :param entity_id: The id of the entity to retrieve the extras for.
        :return: A dictionary with the entity extras.
        """
        return t.cast(
            dict,
            self.entity_class.collection.query(
                filters={'pk': entity_id},
                project=['extras'],
            ).first()[0],
        )

    def create_entity(self, model: EntityModelType) -> EntityModelType:
        """Create new AiiDA entity from its model.

        :param model: The Pydantic model of the entity to create.
        :return: The created and stored AiiDA `Entity` instance.
        """
        entity = self.entity_class.from_model(model).store()
        return self.to_model(entity)

    def to_model(self, entity: EntityType) -> EntityModelType:
        """Convert an AiiDA entity to its Pydantic model.

        :param entity: The AiiDA entity to convert.
        :return: The Pydantic model of the entity, excluding any fields specified in `excluded_fields`.
        """
        return t.cast(EntityModelType, entity.to_model(minimal=True))
