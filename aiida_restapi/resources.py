from typing import Union

from aiida.common.exceptions import EntryPointError, LoadingEntryPointError
from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

from aiida_restapi.exceptions import RestFeatureNotAvailable, RestInputValidationError
from aiida_restapi.identifiers import construct_full_type, load_entry_point_from_full_type


def get_all_download_formats(full_type: Union[str, None] = None) -> dict:
    """Returns dict of possible node formats for all available node types"""
    all_formats = {}

    if full_type:
        try:
            node_cls = load_entry_point_from_full_type(full_type)
        except (TypeError, ValueError):
            raise RestInputValidationError(f'The full type {full_type} is invalid.')
        except EntryPointError:
            raise RestFeatureNotAvailable('The download formats for this node type are not available.')

        try:
            available_formats = node_cls.get_export_formats()
            all_formats[full_type] = available_formats
        except AttributeError:
            pass
    else:
        entry_point_group = 'aiida.data'

        for name in get_entry_point_names(entry_point_group):
            try:
                node_cls = load_entry_point(entry_point_group, name)
                available_formats = node_cls.get_export_formats()
            except (AttributeError, LoadingEntryPointError):
                continue

            if available_formats:
                full_type = construct_full_type(node_cls.class_node_type, '')
                all_formats[full_type] = available_formats

    return all_formats
