# -*- coding: utf-8 -*-
"""Utility functions for graphql."""
# pylint: disable=unused-argument,too-many-arguments

import datetime
from typing import Iterator, List

import graphene as gr
from dateutil.parser import parser as date_parser
from graphene.types.generic import GenericScalar
from graphql.language import ast


class JSON(GenericScalar):
    """
    Subclass of the  `GenericScalar` scalar type represents a generic
    GraphQL scalar value that could be:
    String, Boolean, Int, Float, List or Object.
    """


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
