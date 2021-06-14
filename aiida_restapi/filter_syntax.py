# -*- coding: utf-8 -*-
"""Defines an EBNF Grammar, for parsing a QueryBuilder filter string.

This grammar was originally adapted from:
https://github.com/Materials-Consortia/OPTIMADE/blob/master/optimade.rst#the-filter-language-ebnf-grammar
"""
from importlib import resources
from typing import Any, Callable, Dict, List, Optional, Union

from lark import Lark, Token, Tree

from . import static
from .utils import parse_date

FILTER_GRAMMAR = resources.open_text(static, "filter_grammar.lark")

FILTER_PARSER = Lark(FILTER_GRAMMAR, start="filter")

_convertors: Dict[str, Callable[[str], Any]] = {
    "FLOAT": float,
    "STRING": lambda s: s[1:-1],
    "PROPERTY": str,
    "INTEGER": int,
    "DIGITS": int,
    "DATE": parse_date,
    "TIME": parse_date,
    "DATETIME": parse_date,
}


def _parse_value(value: Token) -> Union[int, float, str]:
    """Parse a value token"""
    return _convertors[value.type](value.value)


def _parse_valuelist(valuelist: Tree) -> List[Union[int, float, str]]:
    """Parse a valuelist tree."""
    output = []
    for child in valuelist.children:
        try:
            if child.data != "value":
                continue
        except AttributeError:
            continue
        output.append(_parse_value(child.children[0]))
    return output


def parse_filter_str(string: Optional[str]) -> Dict[str, Any]:
    """Parse a filter string to a list of ``QueryBuilder`` compliant operators."""
    filters: Dict[str, Any] = {}
    if not string:
        return filters
    try:
        tree = FILTER_PARSER.parse(string)
    except Exception as err:
        raise ValueError(f"Malformed filter string: {err}") from err

    for child in tree.children:
        try:
            if child.data != "comparison":
                continue
        except AttributeError:
            continue
        # the first child will always be the property
        prop_token, rhs_tree = child.children[:2]
        # the first child will always be the comparator
        rhs_compare = rhs_tree.children[0]
        # parse the comparator
        value: Any
        if rhs_compare.data == "value_op_rhs":
            operator = rhs_compare.children[0].value.strip()
            value = _parse_value(rhs_compare.children[1].children[0])
        elif rhs_compare.data == "fuzzy_string_op_rhs":
            operator = rhs_compare.children[0].type.lower()
            value = _parse_value(rhs_compare.children[-1])
        elif rhs_compare.data == "length_op_rhs":
            operator = "of_length"
            value = _parse_value(rhs_compare.children[-1])
        elif rhs_compare.data == "contains_op_rhs":
            operator = "contains"
            value = _parse_valuelist(rhs_compare.children[-1])
        elif rhs_compare.data == "is_in_op_rhs":
            operator = "in"
            value = _parse_valuelist(rhs_compare.children[-1])
        elif rhs_compare.data == "has_op_rhs":
            operator = "has_key"
            value = _parse_value(rhs_compare.children[-1])
        else:
            raise ValueError(f"Unknown comparison: {rhs_compare.data}")
        # TODO if prop_token.value in filters, turn int "and"
        filters[prop_token.value] = {operator: value}
    return filters
