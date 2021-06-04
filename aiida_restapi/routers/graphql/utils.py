# -*- coding: utf-8 -*-
# pylint: disable=unused-argument

import datetime
from typing import Any, Dict, Iterator, List, Type

import graphene as gr
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from dateutil.parser import parser as date_parser
from graphene.types.generic import GenericScalar
from graphql import GraphQLError
from graphql.language import ast

ENTITY_LIMIT = 100
"""The maximum query limit allowed for a list of entities."""


class JSON(GenericScalar):
    """
    Subclass of the  `GenericScalar` scalar type represents a generic
    GraphQL scalar value that could be:
    String, Boolean, Int, Float, List or Object.
    """


def make_entities_cls(
    entity_cls: Type[gr.ObjectType], orm_cls: Type[orm.Entity], name: str
) -> Type[gr.ObjectType]:
    """Return a class with standard fields/resolvers for querying multiple rows of the same entity."""

    # TODO is this the best way to achieve this?
    # it is a bit annoying because you need to have variable class attributes
    # and staticmethods, so I did not see an easy way to do this with simple subclassing
    class Entities(gr.ObjectType):

        count = gr.Int(description=f"Total number of rows of {name}")
        rows = gr.List(
            entity_cls,
            limit=gr.Int(
                default_value=ENTITY_LIMIT,
                description=f"Maximum number of rows to return (no more than {ENTITY_LIMIT}",
            ),
            offset=gr.Int(default_value=0, description="Skip the first n rows"),
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
        def resolve_rows(
            parent: Any,
            info: gr.ResolveInfo,
            limit: int,
            offset: int,
        ) -> List[Dict[str, Any]]:
            """Return a list of field dicts, for the entity class to resolve.

            :param limit: Set the limit (nr of rows to return)
            :param
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
            return [d["fields"] for d in query.dict()]

    return Entities


def parse_date(string: str) -> datetime.datetime:
    """Parse any date/time stamp string."""
    return date_parser().parse(string)


def selected_field_names_naive(selection_set: ast.SelectionSet) -> Iterator[str]:
    """Get the list of field names that are selected at the current level.
    Does not include nested names.

    Taken from: https://github.com/graphql-python/graphene/issues/57#issuecomment-774227086
    """
    assert isinstance(selection_set, ast.SelectionSet)

    for node in selection_set.selections:
        # Field
        if isinstance(node, ast.Field):
            yield node.name.value
        # Fragment spread (`... fragmentName`)
        elif isinstance(node, (ast.FragmentSpread, ast.InlineFragment)):
            raise NotImplementedError(
                "Fragments are not supported by this simplistic function"
            )
        else:
            raise NotImplementedError(str(type(node)))


def get_projection(info: gr.ResolveInfo) -> List[str]:
    """Traverse the child AST, to work out what fields we should project.

    To distinguish database fields from joined entities, we use the simple heuristic
    that fields are lowercase and joins are uppercase.
    If any joins are present, we always include "id", so they can be linked.

    We fallback to "**" (all fields) if the selection set cannot be identified.
    """
    try:
        selected = set(selected_field_names_naive(info.field_asts[0].selection_set))
        fields = {s for s in selected if s and s[0].islower()}
        joins = [s for s in selected if s and s[0].isupper()]
        if joins:
            fields.add("id")
        return list(fields)
    except NotImplementedError:
        return ["**"]
