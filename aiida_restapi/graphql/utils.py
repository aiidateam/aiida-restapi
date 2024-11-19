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

    @staticmethod
    def serialize(value: Any) -> Any:
        """Serialize the value to JSON format.

        Args:
            value: The value to serialize

        Returns:
            The serialized value
        """
        return value

    @staticmethod
    def parse_literal(node: ast.ValueNode) -> Any:
        """Parse a literal value from a GraphQL AST node.

        Args:
            node: The AST node to parse

        Returns:
            The parsed value, or None if parsing fails
        """
        if isinstance(node, ast.StringValue):
            return node.value
        return None

    @staticmethod
    def parse_value(value: Any) -> Any:
        """Parse a value from a GraphQL input.

        Args:
            value: The value to parse

        Returns:
            The parsed value
        """
        return value


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
