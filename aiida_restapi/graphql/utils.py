# -*- coding: utf-8 -*-
"""Utility functions for graphql."""
# pylint: disable=unused-argument,too-many-arguments


from typing import Any, Iterator

import graphene as gr
from graphene.types.scalars import Scalar
from graphql.language import ast


class JSON(Scalar):
    """
    Custom scalar type for JSON values that could be:
    String, Boolean, Int, Float, List or Object.
    """


class FilterString(gr.String):
    """A string adhering to the AiiDA filter syntax."""


def selected_field_names_naive(selection_set: ast.SelectionSetNode) -> Iterator[str]:
    """Get the list of field names that are selected at the current level.
    Does not include nested names.

    Taken from: https://github.com/graphql-python/graphene/issues/57#issuecomment-774227086
    """
    assert isinstance(selection_set, ast.SelectionSetNode)

    for node in selection_set.selections:
        # Field
        if isinstance(node, ast.FieldNode):
            yield node.name.value
        # Fragment spread (`... fragmentName`)
        elif isinstance(node, (ast.FragmentSpreadNode, ast.InlineFragmentNode)):
            raise NotImplementedError(
                "Fragments are not supported by this simplistic function"
            )
        else:
            raise NotImplementedError(str(type(node)))
