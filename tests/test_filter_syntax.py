# -*- coding: utf-8 -*-
"""Tests for syntax filter."""
import datetime

import pytest

from aiida_restapi.filter_syntax import parse_filter_str


@pytest.mark.parametrize(
    "input_str,output",
    [
        ("a==1", {"a": {"==": 1}}),
        ("a_bc>='d'", {"a_bc": {">=": "d"}}),
        ("a.b<=c", {"a.b": {"<=": "c"}}),
        ("a != 1.0", {"a": {"!=": 1.0}}),
        ("a==2020-01-01", {"a": {"==": datetime.datetime(2020, 1, 1, 0, 0)}}),
        ("a==2020-01-01 10:11", {"a": {"==": datetime.datetime(2020, 1, 1, 10, 11)}}),
        ("a == 1 AND b == 2", {"a": {"==": 1}, "b": {"==": 2}}),
        ('a LIKE "x%"', {"a": {"like": "x%"}}),
        ('a iLIKE "x%"', {"a": {"ilike": "x%"}}),
        ('a iLIKE "x%"', {"a": {"ilike": "x%"}}),
        ("a LENGTH 33", {"a": {"of_length": 33}}),
        ("a OF LENGTH 33", {"a": {"of_length": 33}}),
        ("a IN 1", {"a": {"in": [1]}}),
        ("a IS IN 1", {"a": {"in": [1]}}),
        ("a IN 1,2,3", {"a": {"in": [1, 2, 3]}}),
        ("a IN x,y,z", {"a": {"in": ["x", "y", "z"]}}),
        ('a IN "x","y","z"', {"a": {"in": ["x", "y", "z"]}}),
        ('a HAS "x"', {"a": {"has_key": "x"}}),
        ('a HAS KEY "y"', {"a": {"has_key": "y"}}),
        ("a < 2 & a >=1 & a == 3", {"a": {"and": [{"<": 2}, {">=": 1}, {"==": 3}]}}),
    ],
)
def test_parser(input_str, output):
    """Test correct parsing"""
    assert parse_filter_str(input_str) == output
