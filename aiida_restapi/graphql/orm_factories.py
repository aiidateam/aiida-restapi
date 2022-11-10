# -*- coding: utf-8 -*-
"""Classes and functions to auto-generate base ObjectTypes for aiida orm entities."""
# pylint: disable=unused-argument,redefined-builtin
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Type, Union
from uuid import UUID

import graphene as gr
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from graphql import GraphQLError

from aiida_restapi.aiida_db_mappings import ORM_MAPPING, get_model_from_orm

from .config import ENTITY_LIMIT
from .utils import JSON, selected_field_names_naive

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
    for name, field in get_model_from_orm(cls).__fields__.items():
        if name in exclude_fields:
            continue
        gr_type = _type_mapping[field.type_]
        output[name] = gr_type(description=field.field_info.description)
    return output


def fields_from_name(
    cls: str, exclude_fields: Sequence[str] = ()
) -> Dict[str, gr.Scalar]:
    """Extract the fields from an AIIDA ORM class name and convert them to graphene objects."""
    output = {}
    for name, field in ORM_MAPPING[cls].__fields__.items():
        if name in exclude_fields:
            continue
        gr_type = _type_mapping[field.type_]
        output[name] = gr_type(description=field.field_info.description)
    return output


def field_names_from_orm(cls: Type[orm.Entity]) -> Set[str]:
    """Extract the field names from an AIIDA ORM class."""
    return set(get_model_from_orm(cls).__fields__.keys())


def get_projection(
    db_fields: Set[str], info: gr.ResolveInfo, is_link: bool = False
) -> Union[List[str], str]:
    """Traverse the child AST to work out what fields we should project.

    Any fields found that are not database fields, are assumed to be joins.
    If any joins are present, we always include "id", so they can be linked.

    We fallback to "**" (all fields) if the selection set cannot be identified.
    """
    if is_link:
        # TODO here we need to look deeper under the "node" field
        return "**"
    try:
        selected = set(selected_field_names_naive(info.field_asts[0].selection_set))
        fields = db_fields.intersection(selected)
        joins = db_fields.difference(selected)
        if joins:
            fields.add("id")
        return list(fields)
    except NotImplementedError:
        return "**"


def single_cls_factory(
    orm_cls: Type[orm.Entity], exclude_fields: Sequence[str] = ()
) -> Type[gr.ObjectType]:
    """Create a graphene class with standard fields/resolvers for querying a single AiiDA ORM entity."""
    return type(
        "AiidaOrmObjectType", (gr.ObjectType,), fields_from_orm(orm_cls, exclude_fields)
    )


EntitiesParentType = Optional[Dict[str, Any]]


def create_query_path(
    query: orm.QueryBuilder, parent: Dict[str, Any]
) -> Dict[str, Any]:
    """Append parent entities to the ``QueryBuilder`` path.

    :param parent: data from the parent resolver
    :returns: key-word arguments for the "leaf" path
    """
    leaf_kwargs: Dict[str, Any] = {}
    if "group_id" in parent:
        query.append(orm.Group, filters={"id": parent["group_id"]}, tag="group")
        leaf_kwargs["with_group"] = "group"
    if "edge_type" in parent:
        query.append(
            orm.nodes.Node,
            filters={"id": parent["parent_id"]},
            tag=parent["edge_type"],
        )
        leaf_kwargs[f'with_{parent["edge_type"]}'] = parent["edge_type"]
        if parent.get("project_edge"):
            leaf_kwargs["edge_tag"] = f'{parent["edge_type"]}_edge'
            leaf_kwargs["edge_project"] = "**"
    return leaf_kwargs


def multirow_cls_factory(
    entity_cls: Type[gr.ObjectType], orm_cls: Type[orm.Entity], name: str
) -> Type[gr.ObjectType]:
    """Create a graphene class with standard fields/resolvers for querying multiple rows of the same AiiDA ORM entity."""

    db_fields = field_names_from_orm(orm_cls)

    class AiidaOrmRowsType(gr.ObjectType):
        """A class for querying multiple rows of the same AiiDA ORM entity."""

        count = gr.Int(description=f"Total number of rows of {name}")
        rows = gr.List(
            entity_cls,
            limit=gr.Int(
                default_value=ENTITY_LIMIT,
                description=f"Maximum number of rows to return (no more than {ENTITY_LIMIT})",
            ),
            offset=gr.Int(default_value=0, description="Skip the first n rows"),
            orderBy=gr.String(description="Field to order rows by", default_value="id"),
            orderAsc=gr.Boolean(
                default_value=True,
                description="Sort field in ascending order, else descending.",
            ),
        )

        @with_dbenv()
        @staticmethod
        def resolve_count(parent: EntitiesParentType, info: gr.ResolveInfo) -> int:
            """Count the number of rows, after applying filters parsed down from the parent."""
            parent = parent or {}
            query = orm.QueryBuilder()
            leaf_kwargs = create_query_path(query, parent)
            leaf_kwargs["filters"] = parent.get("filters", None)
            query.append(orm_cls, **leaf_kwargs)
            return query.count()

        @with_dbenv()
        @staticmethod
        def resolve_rows(  # pylint: disable=too-many-arguments
            parent: EntitiesParentType,
            info: gr.ResolveInfo,
            limit: int,
            offset: int,
            orderAsc: bool,
            orderBy: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """Return a list of field dicts, for the entity class to resolve.

            :param parent: The parent fill dictate the query to perform
            :param limit: Set the limit (nr of rows to return)
            :param offset: Skip the first n rows
            :param orderBy: Field to order by
            :param orderAsc: Sort field in ascending order, else descending
            """
            if limit > ENTITY_LIMIT:
                raise GraphQLError(
                    f"{name} 'limit' must be no more than {ENTITY_LIMIT}"
                )
            parent = parent or {}

            # setup the query
            query = orm.QueryBuilder()
            leaf_kwargs = create_query_path(query, parent)
            leaf_kwargs["filters"] = parent.get("filters", None)
            leaf_kwargs["project"] = get_projection(
                db_fields, info, is_link=(parent.get("project_edge") is True)
            )
            leaf_kwargs["tag"] = "fields"
            query.append(orm_cls, **leaf_kwargs)

            # setup returned rows configuration of the query
            query.distinct()
            query.offset(offset)
            query.limit(limit)
            if orderBy:
                query.order_by({"fields": {orderBy: "asc" if orderAsc else "desc"}})

            # run query
            if parent.get("project_edge") is True:
                return [
                    {"node": d["fields"], "link": d[f'{parent["edge_type"]}_edge']}
                    for d in query.dict()
                ]
            return [d["fields"] for d in query.dict()]

    return AiidaOrmRowsType


ENTITY_DICT_TYPE = Optional[Dict[str, Any]]


@with_dbenv()
def resolve_entity(
    orm_cls: orm.Entity,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
    uuid_name: str = "uuid",
) -> ENTITY_DICT_TYPE:
    """Query for a single entity, and project only the fields requested.

    :param uuid_name: This is used for User, where we set it to "email"
    """
    filters: Dict[str, Union[str, int]]
    if id is not None:
        assert uuid is None, f"Only one of id or {uuid_name} can be specified"
        filters = {"id": id}
    elif uuid is not None:
        filters = {uuid_name: uuid}
    else:
        raise AssertionError(f"One of id or {uuid_name} must be specified")

    db_fields = field_names_from_orm(orm_cls)
    project = get_projection(db_fields, info)
    entities = (
        orm.QueryBuilder()
        .append(orm_cls, tag="result", filters=filters, project=project)
        .dict()
    )
    if not entities:
        return None
    return entities[0]["result"]
