###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to work with node "full types" which identify node types.

A node's `full_type` is defined as a string that uniquely defines the node type. A valid `full_type` is constructed by
concatenating the `node_type` and `process_type` of a node with the `FULL_TYPE_CONCATENATOR`. Each segment of the full
type can optionally be terminated by a single `LIKE_OPERATOR_CHARACTER` to indicate that the `node_type` or
`process_type` should start with that value but can be followed by any amount of other characters. A full type is
invalid if it does not contain exactly one `FULL_TYPE_CONCATENATOR` character. Additionally, each segment can contain
at most one occurrence of the `LIKE_OPERATOR_CHARACTER` and it has to be at the end of the segment.

Examples of valid full types:

    'data.bool.Bool.|'
    'process.calculation.calcfunction.%|%'
    'process.calculation.calcjob.CalcJobNode.|aiida.calculations:arithmetic.add'
    'process.calculation.calcfunction.CalcFunctionNode.|aiida.workflows:codtools.primitive_structure_from_cif'

Examples of invalid full types:

    'data.bool'  # Only a single segment without concatenator
    'data.|bool.Bool.|process.'  # More than one concatenator
    'process.calculation%.calcfunction.|aiida.calculations:arithmetic.add'  # Like operator not at end of segment
    'process.calculation%.calcfunction.%|aiida.calculations:arithmetic.add'  # More than one operator in segment

"""

from typing import Any

from aiida.common.escaping import escape_for_sql_like

FULL_TYPE_CONCATENATOR = '|'
LIKE_OPERATOR_CHARACTER = '%'
DEFAULT_NAMESPACE_LABEL = '~no-entry-point~'


def validate_full_type(full_type: str) -> None:
    """Validate that the `full_type` is a valid full type unique node identifier.

    :param full_type: a `Node` full type
    :raises ValueError: if the `full_type` is invalid
    :raises TypeError: if the `full_type` is not a string type
    """
    from aiida.common.lang import type_check

    type_check(full_type, str)

    if FULL_TYPE_CONCATENATOR not in full_type:
        raise ValueError(
            f'full type `{full_type}` does not include the required concatenator symbol `{FULL_TYPE_CONCATENATOR}`.'
        )
    elif full_type.count(FULL_TYPE_CONCATENATOR) > 1:
        raise ValueError(
            f'full type `{full_type}` includes the concatenator symbol `{FULL_TYPE_CONCATENATOR}` more than once.'
        )


def construct_full_type(node_type: str, process_type: str) -> str:
    """Return the full type, which fully identifies the type of any `Node` with the given `node_type` and
    `process_type`.

    :param node_type: the `node_type` of the `Node`
    :param process_type: the `process_type` of the `Node`
    :return: the full type, which is a unique identifier
    """
    if node_type is None:
        node_type = ''

    if process_type is None:
        process_type = ''

    return f'{node_type}{FULL_TYPE_CONCATENATOR}{process_type}'


def get_full_type_filters(full_type: str) -> dict[str, Any]:
    """Return the `QueryBuilder` filters that will return all `Nodes` identified by the given `full_type`.

    :param full_type: the `full_type` node type identifier
    :return: dictionary of filters to be passed for the `filters` keyword in `QueryBuilder.append`
    :raises ValueError: if the `full_type` is invalid
    :raises TypeError: if the `full_type` is not a string type
    """
    validate_full_type(full_type)

    filters: dict[str, Any] = {}
    node_type, process_type = full_type.split(FULL_TYPE_CONCATENATOR)

    for entry in (node_type, process_type):
        if entry.count(LIKE_OPERATOR_CHARACTER) > 1:
            raise ValueError(f'full type component `{entry}` contained more than one like-operator character')

        if LIKE_OPERATOR_CHARACTER in entry and entry[-1] != LIKE_OPERATOR_CHARACTER:
            raise ValueError(f'like-operator character in full type component `{entry}` is not at the end')

    if LIKE_OPERATOR_CHARACTER in node_type:
        # Remove the trailing `LIKE_OPERATOR_CHARACTER`, escape the string and reattach the character
        node_type = node_type[:-1]
        node_type = escape_for_sql_like(node_type) + LIKE_OPERATOR_CHARACTER
        filters['node_type'] = {'like': node_type}
    else:
        filters['node_type'] = {'==': node_type}

    if LIKE_OPERATOR_CHARACTER in process_type:
        # Remove the trailing `LIKE_OPERATOR_CHARACTER` ()
        # If that was the only specification, just ignore this filter (looking for any process_type)
        # If there was more: escape the string and reattach the character
        process_type = process_type[:-1]
        if process_type:
            process_type = escape_for_sql_like(process_type) + LIKE_OPERATOR_CHARACTER
            filters['process_type'] = {'like': process_type}
    elif process_type:
        filters['process_type'] = {'==': process_type}
    else:
        # A `process_type=''` is used to represents both `process_type='' and `process_type=None`.
        # This is because there is no simple way to single out null `process_types`, and therefore
        # we consider them together with empty-string process_types.
        # Moreover, the existence of both is most likely a bug of migrations and thus both share
        # this same "erroneous" origin.
        filters['process_type'] = {'or': [{'==': ''}, {'==': None}]}

    return filters


def load_entry_point_from_full_type(full_type: str) -> Any:
    """Return the loaded entry point for the given `full_type` unique node type identifier.

    :param full_type: the `full_type` unique node type identifier
    :raises ValueError: if the `full_type` is invalid
    :raises TypeError: if the `full_type` is not a string type
    :raises `~aiida.common.exceptions.EntryPointError`: if the corresponding entry point cannot be loaded
    """
    from aiida.common import EntryPointError
    from aiida.common.utils import strip_prefix
    from aiida.plugins.entry_point import (
        is_valid_entry_point_string,
        load_entry_point,
        load_entry_point_from_string,
    )

    data_prefix = 'data.'

    validate_full_type(full_type)

    node_type, process_type = full_type.split(FULL_TYPE_CONCATENATOR)

    if is_valid_entry_point_string(process_type):
        try:
            return load_entry_point_from_string(process_type)
        except EntryPointError:
            raise EntryPointError(f'could not load entry point `{process_type}`')

    elif node_type.startswith(data_prefix):
        base_name = strip_prefix(node_type, data_prefix)
        entry_point_name = base_name.rsplit('.', 2)[0]

        try:
            return load_entry_point('aiida.data', entry_point_name)
        except EntryPointError:
            raise EntryPointError(f'could not load entry point `{process_type}`')

    # Here we are dealing with a `ProcessNode` with a `process_type` that is not an entry point string.
    # Which means it is most likely a full module path (the fallback option) and we cannot necessarily load the
    # class from this. We could try with `importlib` but not sure that we should
    raise EntryPointError('entry point of the given full type cannot be loaded')
