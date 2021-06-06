# -*- coding: utf-8 -*-
"""Classes and functions to auto-generate base ObjectTypes for aiida orm entities."""
# pylint: disable=unused-argument
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Type
from uuid import UUID

import graphene as gr
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from graphql import GraphQLError

from aiida_restapi.orm_mappings import ORM_MAPPING

from .config import ENTITY_LIMIT
from .utils import JSON, get_projection

_type_mapping = {
    int: gr.Int,
    float: gr.Float,
    str: gr.String,
    bool: gr.Boolean,
    datetime: gr.DateTime,
    UUID: gr.ID,
    Any: JSON,
}


def fields_from_orm(
    cls: Type[orm.Entity], exclude_fields: Sequence[str] = ()
) -> Dict[str, gr.Scalar]:
    """Extract the fields from an AIIDA ORM class and convert them to graphene objects."""
    output = {}
    for name, field in ORM_MAPPING[cls].__fields__.items():
        if name in exclude_fields:
            continue
        gr_type = _type_mapping[field.type_]
        output[name] = gr_type(description=field.field_info.description)
    return output


def single_cls_factory(
    orm_cls: Type[orm.Entity], exclude_fields: Sequence[str] = ()
) -> Type[gr.ObjectType]:
    """Create a graphene class with standard fields/resolvers for querying a single AiiDA ORM entity."""
    return type(
        "AiidaOrmObjectType", (gr.ObjectType,), fields_from_orm(orm_cls, exclude_fields)
    )


def multirow_cls_factory(
    entity_cls: Type[gr.ObjectType], orm_cls: Type[orm.Entity], name: str
) -> Type[gr.ObjectType]:
    """Create a graphene class with standard fields/resolvers for querying multiple rows of the same AiiDA ORM entity."""

    class AiidaOrmRowsType(gr.ObjectType):
        """A class for querying multiple rows of the same AiiDA ORM entity."""

        count = gr.Int(description=f"Total number of rows of {name}")
        rows = gr.List(
            entity_cls,
            limit=gr.Int(
                default_value=ENTITY_LIMIT,
                description=f"Maximum number of rows to return (no more than {ENTITY_LIMIT}",
            ),
            offset=gr.Int(default_value=0, description="Skip the first n rows"),
            orderBy=gr.String(description="Field to order rows by"),
            orderAsc=gr.Boolean(
                default_value=True,
                description="Sort field in ascending order, else descending.",
            ),
        )

        @with_dbenv()
        @staticmethod
        def resolve_count(parent: Any, info: gr.ResolveInfo) -> int:
            """Count the number of rows, after applying filters parsed down from the parent."""
            try:
                filters = parent.get("filters")
            except AttributeError:
                filters = None
            query = orm.QueryBuilder().append(orm_cls, filters=filters)
            return query.count()

        @with_dbenv()
        @staticmethod
        def resolve_rows(  # pylint: disable=too-many-arguments
            parent: Any,
            info: gr.ResolveInfo,
            limit: int,
            offset: int,
            orderAsc: bool,
            orderBy: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """Return a list of field dicts, for the entity class to resolve.

            :param limit: Set the limit (nr of rows to return)
            :param offset: Skip the first n rows
            :param orderBy: Field to order by
            :param orderAsc: Sort field in ascending order, else descending
            """
            if limit > ENTITY_LIMIT:
                raise GraphQLError(
                    f"{name} 'limit' must be no more than {ENTITY_LIMIT}"
                )
            project = get_projection(info)
            try:
                filters = parent.get("filters")
            except AttributeError:
                filters = None

            query = orm.QueryBuilder().append(
                orm_cls, tag="fields", filters=filters, project=project
            )
            query.offset(offset)
            query.limit(limit)
            if orderBy:
                query.order_by({"fields": {orderBy: "asc" if orderAsc else "desc"}})
            return [d["fields"] for d in query.dict()]

    return AiidaOrmRowsType


ENTITY_DICT_TYPE = Optional[Dict[str, Any]]


@with_dbenv()
def resolve_entity(
    entity: orm.Entity, info: gr.ResolveInfo, pk: int
) -> ENTITY_DICT_TYPE:
    """Query for a single entity, and project only the fields requested."""
    project = get_projection(info)
    entities = (
        orm.QueryBuilder()
        .append(entity, tag="result", filters={"id": pk}, project=project)
        .dict()
    )
    if not entities:
        return None
    return entities[0]["result"]
