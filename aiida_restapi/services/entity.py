"""REST API entity repository."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.pydantic import get_metadata

from aiida_restapi.common.exceptions import QueryBuilderException
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryBuilderParams
from aiida_restapi.common.types import EntityModelType, EntityType


class EntityService(t.Generic[EntityType, EntityModelType]):
    """Utility class for AiiDA REST API operations.

    This class provides methods to retrieve AiiDA entities with optional filtering, sorting, and pagination.

    :param entity_class: The AiiDA ORM entity class associated with this utility, e.g. `orm.User`, `orm.Node`, etc.
    """

    def __init__(self, entity_class: type[EntityType]) -> None:
        self.entity_class = entity_class
        self.with_key = entity_class.__name__.lower()

    @property
    def project(self) -> list[str]:
        """Get the list of projections to use when querying the AiiDA entity.

        :return: The list of projections to use when querying the AiiDA entity.
        :rtype: list[str]
        """
        if not hasattr(self, '_project'):
            self._project = self._get_projections()
        return self._project

    def get_schema(self, which: t.Literal['get', 'post'] | None = None) -> dict[str, t.Any]:
        """Get JSON schema for the AiiDA entity.

        :param which: The type of schema to retrieve: 'get' or 'post'.
        :type which: str | None
        :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
        :rtype: dict[str, t.Any]
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

    def get_many(self, query_params: QueryBuilderParams) -> PaginatedResults[dict[str, t.Any]]:
        """Get AiiDA entities with optional filtering, sorting, and/or pagination.

        :param query_params: The query parameters for filtering, sorting, and pagination.
        :type query_params: QueryBuilderParams
        :return: The paginated results, including total count, current page, page size, and list of entity models.
        :rtype: PaginatedResults[dict[str, t.Any]
        """
        try:
            total = self.entity_class.collection.count(filters=query_params.filters)
            results = self.entity_class.collection.query(
                filters=query_params.filters,
                order_by=query_params.order_by,
                limit=query_params.page_size,
                offset=query_params.page_size * (query_params.page - 1),
                project=self.project,
            ).dict()
        except Exception as exception:
            raise QueryBuilderException(str(exception)) from exception
        return PaginatedResults(
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            data=[next(iter(result.values())) for result in results],
        )

    def get_one(self, identifier: str | int) -> dict[str, t.Any]:
        """Get an AiiDA entity by id.

        :param identifier: The id of the entity to retrieve.
        :type identifier: str | int
        :return: The AiiDA entity.
        :rtype: dict[str, t.Any]
        """
        result = self.entity_class.collection.query(
            filters={self.entity_class.identity_field: identifier},
            project=self.project,
        ).dict()
        return next(iter(result[0].values()))

    def get_related_one(
        self,
        identifier: str | int,
        related_type: type[orm.Entity],
    ) -> dict[str, t.Any]:
        """Get a related foreign entity of an entity.

        :param identifier: The id of the entity to retrieve the foreign entity for.
        :type identifier: str | int
        :param related_type: The related AiiDA ORM entity class to retrieve.
        :type related_type: type[orm.Entity]
        :return: The related foreign entity.
        :rtype: dict[str, t.Any]
        """
        qb = (
            orm.QueryBuilder()
            .append(
                self.entity_class,
                filters={self.entity_class.identity_field: identifier},
                tag='entity',
            )
            .append(
                related_type,
                joining_keyword=f'with_{self.with_key}',
                joining_value='entity',
                project=self._get_projections(related_type),
            )
        )

        try:
            result = qb.dict()
        except Exception as exception:
            raise QueryBuilderException(str(exception)) from exception

        if not result:
            raise NotExistent(
                f'{related_type.__name__} related to {self.entity_class.__name__}<{identifier}> not found.'
            )

        return next(iter(result[0].values()))

    def get_related_many(
        self,
        identifier: str | int,
        related_type: type[orm.Entity],
        query_params: QueryBuilderParams,
    ) -> PaginatedResults[dict[str, t.Any]]:
        """Get related foreign entities of an entity.

        :param identifier: The id of the entity to retrieve the foreign entities for.
        :type identifier: str | int
        :param related_type: The related AiiDA ORM entity class to retrieve.
        :type related_type: type[orm.Entity]
        :param query_params: The query parameters, including filters, order_by, page_size, and page.
        :type query_params: QueryParams
        :return: The paginated results of related foreign entities.
        :rtype: PaginatedResults[dict[str, t.Any]]
        """
        qb = (
            orm.QueryBuilder(
                limit=query_params.page_size,
                offset=query_params.page_size * (query_params.page - 1),
            )
            .append(
                self.entity_class,
                filters={self.entity_class.identity_field: identifier},
                tag='entity',
            )
            .append(
                related_type,
                joining_keyword=f'with_{self.with_key}',
                joining_value='entity',
                filters=query_params.filters,
                project=self._get_projections(related_type),
                tag='related',
            )
        )

        order_by = {'related': query_params.order_by} if query_params.order_by else {}
        qb.order_by([order_by])

        try:
            total = qb.count()
            results = qb.dict()
        except Exception as exception:
            raise QueryBuilderException(str(exception)) from exception

        return PaginatedResults(
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            data=[next(iter(result.values())) for result in results],
        )

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

    def add_one(self, model: EntityModelType) -> dict[str, t.Any]:
        """Create new AiiDA entity from its model.

        :param model: The Pydantic model of the entity to create.
        :type model: EntityModelType
        :return: The created and stored AiiDA `Entity` instance.
        :rtype: dict[str, t.Any]
        """
        entity = self.entity_class.from_model(model).store()
        return entity.serialize(minimal=True)

    def _get_projections(self, orm_class: type[orm.Entity] | None = None) -> list[str]:
        """Get the list of projections to use when querying the AiiDA entity.

        Exclude fields that may be large.

        :param orm_class: The AiiDA ORM entity class to get the projections for.
        :type orm_class: type[orm.Entity] | None
        :return: The list of projections to use when querying the AiiDA entity.
        :rtype: list[str]
        """
        orm_class = orm_class or self.entity_class
        return [key for key, field in orm_class.Model.model_fields.items() if not get_metadata(field, 'may_be_large')]
