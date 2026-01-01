"""REST API entity repository."""

from __future__ import annotations

import typing as t

from aiida.common.exceptions import NotExistent

from aiida_restapi.common.exceptions import QueryBuilderException
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryParams
from aiida_restapi.common.types import EntityModelType, EntityType


class EntityService(t.Generic[EntityType, EntityModelType]):
    """Utility class for AiiDA REST API operations.

    This class provides methods to retrieve AiiDA entities with optional filtering, sorting, and pagination.

    :param entity_class: The AiiDA ORM entity class associated with this utility, e.g. `orm.User`, `orm.Node`, etc.
    """

    def __init__(self, entity_class: type[EntityType]) -> None:
        self.entity_class = entity_class

    def get_schema(self, which: t.Literal['get', 'post'] | None = None) -> dict:
        """Get JSON schema for the AiiDA entity.

        :param which: The type of schema to retrieve: 'get' or 'post'.
        :type which: str | None
        :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
        :rtype: dict
        :raises ValueError: If the 'which' parameter is not 'get' or 'post'.
        """
        if not which:
            return {
                'get': self.entity_class.Model.model_json_schema(),
                'post': self.entity_class.CreateModel.model_json_schema(),
            }
        elif which == 'post':
            return self.entity_class.CreateModel.model_json_schema()
        else:
            return self.entity_class.Model.model_json_schema()

    def get_projections(self) -> list[str]:
        """Get queryable projections for the AiiDA entity.

        :return: The list of queryable projections for the AiiDA entity.
        :rtype: list[str]
        """
        return self.entity_class.fields.keys()

    def get_many(self, query_params: QueryParams) -> PaginatedResults[EntityModelType]:
        """Get AiiDA entities with optional filtering, sorting, and/or pagination.

        :param query_params: The query parameters, including filters, order_by, page_size, and page.
        :type query_params: QueryParams
        :return: The paginated results, including total count, current page, page size, and list of entity models.
        :rtype: PaginatedResults[EntityModelType]
        """
        try:
            total = self.entity_class.collection.count(filters=query_params.filters)
            results = self.entity_class.collection.find(
                filters=query_params.filters,
                order_by=query_params.order_by,
                limit=query_params.page_size,
                offset=query_params.page_size * (query_params.page - 1),
            )
        except Exception as exception:
            raise QueryBuilderException(str(exception)) from exception
        return PaginatedResults(
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            data=[self._to_model(result) for result in results],
        )

    def get_one(self, identifier: str | int) -> EntityModelType:
        """Get an AiiDA entity by id.

        :param identifier: The id of the entity to retrieve.
        :type identifier: str | int
        :return: The AiiDA entity model, e.g. `orm.User.Model`, `orm.Node.Model`, etc.
        :rtype: EntityModelType
        """
        entity = self.entity_class.collection.get(**{self.entity_class.identity_field: identifier})
        return self._to_model(entity)

    def get_field(self, identifier: str | int, field: str) -> t.Any:
        """Get a specific field of an entity.

        :param identifier: The id of the entity to retrieve the extras for.
        :type identifier: str | int
        :param field: The specific field to retrieve.
        :type field: str
        :return: The value of the specified field.
        :rtype: t.Any
        """
        qb = self.entity_class.collection.query(
            filters={self.entity_class.identity_field: identifier},
            project=[field],
        )

        try:
            result = qb.first()
        except Exception as exception:
            raise QueryBuilderException(str(exception)) from exception

        if not result:
            raise NotExistent(f'{self.entity_class.__name__}<{identifier}> does not exist.')

        return result[0]

    def add_one(self, model: EntityModelType) -> EntityModelType:
        """Create new AiiDA entity from its model.

        :param model: The Pydantic model of the entity to create.
        :type model: EntityModelType
        :return: The created and stored AiiDA `Entity` instance.
        :rtype: EntityModelType
        """
        entity = self.entity_class.from_model(model).store()
        return self._to_model(entity)

    def _to_model(self, entity: EntityType) -> EntityModelType:
        """Convert an AiiDA entity to its Pydantic model.

        :param entity: The AiiDA entity to convert.
        :type entity: EntityType
        :return: The Pydantic model of the entity, excluding any fields specified in `excluded_fields`.
        :rtype: EntityModelType
        """
        return t.cast(EntityModelType, entity.to_model(minimal=True))
