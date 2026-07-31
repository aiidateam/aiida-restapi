"""Tests for REST API query parameter parsing."""

from urllib.parse import urlencode

import pytest
from aiida.common.exceptions import InputValidationError
from starlette.requests import Request

from aiida_restapi.common.query import querybuilder_params


def make_request(params: list[tuple[str, str]]) -> Request:
    """Return a request with the given query parameters."""
    return Request({'type': 'http', 'method': 'GET', 'path': '/nodes', 'query_string': urlencode(params).encode()})


def parse(params: list[tuple[str, str]]):
    """Parse query parameters using defaults for sorting and pagination."""
    return querybuilder_params(make_request(params))


@pytest.mark.parametrize(
    'parameter,operator',
    [
        ('filter[value]', '=='),
        ('filter[value][==]', '=='),
        ('filter[value][!==]', '!=='),
        ('filter[value][<]', '<'),
        ('filter[value][<=]', '<='),
        ('filter[value][>]', '>'),
        ('filter[value][>=]', '>='),
        ('filter[value][like]', 'like'),
        ('filter[value][ilike]', 'ilike'),
        ('filter[value][of_length]', 'of_length'),
        ('filter[value][shorter]', 'shorter'),
        ('filter[value][longer]', 'longer'),
        ('filter[value][has_key]', 'has_key'),
    ],
)
def test_filter_operators(parameter: str, operator: str):
    """Test mapping HTTP filter operators to QueryBuilder operators."""
    raw = '2' if operator in {'<', '<=', '>', '>=', 'of_length', 'shorter', 'longer'} else 'value'
    assert parse([(parameter, raw)]).filters == {'value': {operator: 2 if raw == '2' else raw}}


def test_filter_typed_values_and_dot_path():
    """Test JSON scalar decoding and nested dictionary dot paths."""
    result = parse(
        [
            ('filter[attributes.config.enabled]', 'true'),
            ('filter[attributes.config.timeout][>=]', '30'),
        ]
    )
    assert result.filters == {
        'attributes.config.enabled': {'==': True},
        'attributes.config.timeout': {'>=': 30},
    }


def test_filter_in_json_list():
    """Test membership filters accept JSON lists."""
    assert parse([('filter[value][in]', '[1, 2, 3]')]).filters == {'value': {'in': [1, 2, 3]}}
    assert parse([('filter[value][in]', '["blah", "bl,ah"]')]).filters == {'value': {'in': ['blah', 'bl,ah']}}


def test_filter_contains_json_list():
    """Test array containment filters accept JSON lists."""
    assert parse([('filter[value][contains]', '["one", 2, true]')]).filters == {'value': {'contains': ['one', 2, True]}}


@pytest.mark.parametrize('operator', ['in', '!in', 'contains', '!contains'])
@pytest.mark.parametrize('value', ['', 'one,two', '"one"', '1', '{}'])
def test_filter_list_requires_json_list(operator: str, value: str):
    """Test list operators reject malformed JSON and non-list values."""
    with pytest.raises(InputValidationError, match='requires a JSON list'):
        parse([(f'filter[value][{operator}]', value)])


@pytest.mark.parametrize('operator', ['in', '!in', 'contains', '!contains'])
def test_filter_list_requires_values(operator: str):
    """Test list operators reject an empty JSON list."""
    with pytest.raises(InputValidationError, match='requires at least one value'):
        parse([(f'filter[value][{operator}]', '[]')])


def test_filter_repeated_in():
    """Test repeated membership filters are flattened."""
    result = parse([('filter[value][in]', '["one", "two"]'), ('filter[value][in]', '["three"]')])
    assert result.filters == {'value': {'in': ['one', 'two', 'three']}}


def test_filter_contains_and_repeated_constraints():
    """Test structural containment and AND aggregation of repeated constraints."""
    result = parse(
        [
            ('filter[attributes.tags][contains]', '["one"]'),
            ('filter[attributes.tags][contains]', '["two"]'),
        ]
    )
    assert result.filters == {
        'attributes.tags': {'and': [{'contains': ['one']}, {'contains': ['two']}]},
    }


def test_filter_negation():
    """Test leaf negation."""
    result = parse(
        [
            ('filter[label][!like]', 'test%'),
            ('filter[pk][!==]', '2'),
        ]
    )
    assert result.filters == {'label': {'!like': 'test%'}, 'pk': {'!==': 2}}


@pytest.mark.parametrize(
    'parameter',
    ['filter', 'filter[]', 'filter[value][unknown]', 'filter[value][!]'],
)
def test_invalid_filter_parameter(parameter: str):
    """Test malformed filters and unknown operators are rejected."""
    with pytest.raises(InputValidationError):
        parse([(parameter, 'value')])


def test_sort():
    """Test ascending and descending sort fields."""
    result = querybuilder_params(make_request([('sort', 'label,-ctime')]), sort='label,-ctime')
    assert result.order_by == {'label': 'asc', 'ctime': 'desc'}
