# -*- coding: utf-8 -*-
"""Module defining the graphql plugin mechanism."""
from typing import Any, Callable, Dict, NamedTuple, Sequence, Type, Union

import graphene as gr

# TODO it would be ideal if this was more specific, i.e.
# func(parent: Any, info: gr.ResolveInfo, **kwargs: Any): ...
ResolverType = Callable[..., Any]


class QueryPlugin(NamedTuple):
    """Define a top-level query, to plugin to the schema."""

    name: str
    field: gr.ObjectType
    resolver: ResolverType


def create_query(
    queries: Sequence[QueryPlugin], docstring: str = "The root query"
) -> Type[gr.ObjectType]:
    """Generate a query from a sequence of query plugins."""
    # check that there are no duplicate names
    name_map: Dict[str, QueryPlugin] = {}
    # construct the dict of attributes/methods on the class
    attr_map: Dict[str, Union[gr.ObjectType, ResolverType]] = {}
    for query in queries:
        if query.name.startswith("resolve_"):
            raise ValueError("Plugin name cannot")
        if query.name in name_map:
            raise ValueError(
                f"Duplicate plugin name '{query.name}': {query} and {name_map[query.name]}"
            )
        name_map[query.name] = query
        attr_map[query.name] = query.field
        attr_map[f"resolve_{query.name}"] = query.resolver
    attr_map["__doc__"] = docstring
    return type("RootQuery", (gr.ObjectType,), attr_map)


def create_schema(
    queries: Sequence[QueryPlugin],
    docstring: str = "The root query",
    auto_camelcase: bool = False,
    **kwargs: Any,
) -> gr.Schema:
    """Generate a schema from a sequence of query plugins.

    Note we set auto_camelcase False, since this keeps database field names the same.
    """
    return gr.Schema(
        query=create_query(queries, docstring), auto_camelcase=auto_camelcase, **kwargs
    )
