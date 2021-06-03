# -*- coding: utf-8 -*-
import datetime
from typing import Iterator, List

import graphene as gr
from dateutil.parser import parser as date_parser
from graphql.language import ast


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


def get_projection(info: gr.ResolveInfo, joined: List[str] = ()) -> List[str]:
    try:
        fields = set(selected_field_names_naive(info.field_asts[0].selection_set))
        fields.difference_update(joined)
        if joined:
            fields.add("id")
        return list(fields)
    except NotImplementedError:
        return ["**"]
