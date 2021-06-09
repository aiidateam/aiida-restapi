# -*- coding: utf-8 -*-
"""Utility functions for graphql."""
# pylint: disable=unused-argument,too-many-arguments


from typing import Iterator

import graphene as gr
from graphene.types.generic import GenericScalar
from graphql.language import ast


class JSON(GenericScalar):
    """
    Subclass of the  `GenericScalar` scalar type represents a generic
    GraphQL scalar value that could be:
    String, Boolean, Int, Float, List or Object.
    """


class FilterString(gr.String):
    """A string adhering to the AiiDA filter syntax."""


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
