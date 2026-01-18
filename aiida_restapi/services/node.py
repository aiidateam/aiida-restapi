"""REST API node repository."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.common import EntryPointError, exceptions
from aiida.common.escaping import escape_for_sql_like
from aiida.common.lang import type_check
from aiida.orm.utils import load_node_class
from aiida.plugins.entry_point import (
    get_entry_point_names,
    is_valid_entry_point_string,
    load_entry_point,
    load_entry_point_from_string,
)
from aiida.repository import File

from aiida_restapi.common.exceptions import QueryBuilderException
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryBuilderParams
from aiida_restapi.common.types import NodeModelType, NodeType
from aiida_restapi.config import API_CONFIG

from .entity import EntityService

if t.TYPE_CHECKING:
    from fastapi import UploadFile


class NodeService(EntityService[NodeType, NodeModelType]):
    """Utility class for AiiDA Node REST API operations."""

    FULL_TYPE_CONCATENATOR = '|'
    LIKE_OPERATOR_CHARACTER = '%'
    DEFAULT_NAMESPACE_LABEL = '~no-entry-point~'

    with_key = 'node'

    def get_projections(self, node_type: str | None = None) -> list[str]:
        """Get projectable properties for the AiiDA entity.

        :param node_type: The AiiDA node type.
        :type node_type: str | None
        :return: The list of projectable properties for the AiiDA node.
        :rtype: list[str]
        """
        if not node_type:
            return super().get_projections()
        else:
            node_cls = self._load_entry_point_from_node_type(node_type)
            return sorted(node_cls.fields.keys())

    def get_download_formats(self, full_type: str | None = None) -> dict:
        """Returns dict of possible node formats for all available node types.

        :param full_type: The full type of the AiiDA node.
        :type full_type: str | None
        :return: A dictionary with full types as keys and list of available formats as values.
        :rtype: dict[str, list[str]]
        """
        all_formats = {}

        if full_type:
            node_cls = self._load_entry_point_from_full_type(full_type)
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
                except (AttributeError, exceptions.LoadingEntryPointError):
                    continue

                if available_formats:
                    full_type = self._construct_full_type(node_cls.class_node_type, '')
                    all_formats[full_type] = available_formats

        return all_formats

    def get_repository_metadata(self, uuid: str) -> dict[str, dict]:
        """Get the repository metadata of a node.

        :param uuid: The uuid of the node to retrieve the repository metadata for.
        :type uuid: str
        :return: A dictionary with the repository file metadata.
        :rtype: dict[str, dict]
        """
        node = self.entity_class.collection.get(uuid=uuid)
        total_size = 0

        def get_metadata(objects: list[File], path: str | None = None) -> dict[str, dict]:
            nonlocal total_size

            content: dict = {}

            for obj in objects:
                obj_name = f'{path}/{obj.name}' if path else obj.name
                if obj.is_dir():
                    content[obj.name] = {
                        'type': 'DIRECTORY',
                        'objects': get_metadata(
                            node.base.repository.list_objects(obj_name),
                            obj_name,
                        ),
                    }
                elif obj.is_file():
                    size = node.base.repository.get_object_size(obj_name)

                    binary = False
                    try:
                        with node.base.repository.open(obj_name, 'rb') as f:
                            binary = b'\x00' in f.read(8192)
                            f.seek(0)
                    except (UnicodeDecodeError, TypeError):
                        binary = True

                    content[obj.name] = {
                        'type': 'FILE',
                        'binary': binary,
                        'size': size,
                        'download': f'{API_CONFIG["PREFIX"]}/nodes/{uuid}/repo/contents?filename={obj_name}',
                    }
                    total_size += size

            return content

        metadata = get_metadata(node.base.repository.list_objects())

        if total_size:
            metadata['zipped'] = {
                'type': 'FILE',
                'binary': True,
                'size': total_size,
                'download': f'{API_CONFIG["PREFIX"]}/nodes/{uuid}/repo/contents',
            }

        return metadata

    def get_links(
        self,
        uuid: str,
        direction: t.Literal['incoming', 'outgoing'],
        query_params: QueryBuilderParams = QueryBuilderParams(),
    ) -> PaginatedResults[dict[str, t.Any]]:
        """Get the incoming links of a node.

        :param uuid: The uuid of the node to retrieve the incoming links for.
        :type uuid: str
        :param query_params: The query parameters for filtering, sorting, and pagination.
        :type query_params: QueryBuilderParams
        :param direction: Specify whether to retrieve incoming or outgoing links.
        :type direction: str
        :return: The paginated requested linked nodes.
        :rtype: PaginatedResults[dict[str, t.Any]]
        """
        qb = (
            orm.QueryBuilder(
                limit=query_params.page_size,
                offset=query_params.page_size * (query_params.page - 1),
            )
            .append(
                orm.Node,
                filters=query_params.filters,
                project='uuid',
                tag='link',
            )
            .append(
                self.entity_class,
                filters={self.entity_class.identity_field: uuid},
                joining_keyword=f'with_{direction}',
                joining_value='link',
                edge_project=['label', 'type'],
                tag='node',
            )
        )

        order_by = {'link': query_params.order_by} if query_params.order_by else {}
        qb.order_by([order_by])

        try:
            total = qb.count()
            results = qb.all()
        except Exception as exception:
            raise QueryBuilderException(str(exception)) from exception

        return PaginatedResults(
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            data=[
                {
                    'id': f'{uuid}:{target_uuid}',
                    'source': uuid,
                    'target': target_uuid,
                    'link_label': link_label,
                    'link_type': link_type,
                }
                for target_uuid, link_label, link_type in results
            ],
        )

    def add_one(
        self,
        model: NodeModelType,
        files: dict[str, UploadFile] | None = None,
    ) -> dict[str, t.Any]:
        """Create new AiiDA node from its model.

        :param node_model: The AiiDA ORM model of the node to create.
        :type model: NodeModelType
        :param files: Optional list of files to attach to the node.
        :type files: dict[str, UploadFile] | None
        :return: The created and stored AiiDA node instance.
        :rtype: dict[str, t.Any]
        """
        node_cls = self._load_entry_point_from_node_type(model.node_type)
        node = t.cast(NodeType, node_cls.from_model(model))
        for path, upload in (files or {}).items():
            upload.file.seek(0)
            node.base.repository.put_object_from_filelike(upload.file, path)
        node.store()
        return node.serialize(minimal=True)

    def _validate_full_type(self, full_type: str) -> None:
        """Validate that the `full_type` is a valid full type unique node identifier.

        :param full_type: a `Node` full type
        :type full_type: str
        :raises ValueError: if the `full_type` is invalid
        :raises TypeError: if the `full_type` is not a string type
        """

        type_check(full_type, str)

        if self.FULL_TYPE_CONCATENATOR not in full_type:
            raise ValueError(
                f'full type `{full_type}` does not include the required concatenator symbol '
                f'`{self.FULL_TYPE_CONCATENATOR}`.'
            )
        elif full_type.count(self.FULL_TYPE_CONCATENATOR) > 1:
            raise ValueError(
                f'full type `{full_type}` includes the concatenator symbol '
                f'`{self.FULL_TYPE_CONCATENATOR}` more than once.'
            )

    def _construct_full_type(self, node_type: str, process_type: str) -> str:
        """Return the full type, which fully identifies the type of any `Node` with the given `node_type` and
        `process_type`.

        :param node_type: the `node_type` of the `Node`
        :type node_type: str
        :param process_type: the `process_type` of the `Node`
        :type process_type: str
        :return: the full type, which is a unique identifier
        :rtype: str
        """
        if node_type is None:
            node_type = ''

        if process_type is None:
            process_type = ''

        return f'{node_type}{self.FULL_TYPE_CONCATENATOR}{process_type}'

    def _get_full_type_filters(self, full_type: str) -> dict[str, t.Any]:
        """Return the `QueryBuilder` filters that will return all `Nodes` identified by the given `full_type`.

        :param full_type: the `full_type` node type identifier
        :type full_type: str
        :return: dictionary of filters to be passed for the `filters` keyword in `QueryBuilder.append`
        :rtype: dict[str, t.Any]
        :raises ValueError: if the `full_type` is invalid
        :raises TypeError: if the `full_type` is not a string type
        """
        self._validate_full_type(full_type)

        filters: dict[str, t.Any] = {}
        node_type, process_type = full_type.split(self.FULL_TYPE_CONCATENATOR)

        for entry in (node_type, process_type):
            if entry.count(self.LIKE_OPERATOR_CHARACTER) > 1:
                raise ValueError(f'full type component `{entry}` contained more than one like-operator character')

            if self.LIKE_OPERATOR_CHARACTER in entry and entry[-1] != self.LIKE_OPERATOR_CHARACTER:
                raise ValueError(f'like-operator character in full type component `{entry}` is not at the end')

        if self.LIKE_OPERATOR_CHARACTER in node_type:
            # Remove the trailing `LIKE_OPERATOR_CHARACTER`, escape the string and reattach the character
            node_type = node_type[:-1]
            node_type = escape_for_sql_like(node_type) + self.LIKE_OPERATOR_CHARACTER
            filters['node_type'] = {'like': node_type}
        else:
            filters['node_type'] = {'==': node_type}

        if self.LIKE_OPERATOR_CHARACTER in process_type:
            # Remove the trailing `LIKE_OPERATOR_CHARACTER` ()
            # If that was the only specification, just ignore this filter (looking for any process_type)
            # If there was more: escape the string and reattach the character
            process_type = process_type[:-1]
            if process_type:
                process_type = escape_for_sql_like(process_type) + self.LIKE_OPERATOR_CHARACTER
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

    def _load_entry_point_from_node_type(self, node_type: str) -> NodeType:
        """Return the loaded entry point for the given `node_type`.

        :param node_type: the `node_type` unique node type identifier
        :type node_type: str
        :return: the loaded entry point
        :rtype: NodeType
        :raises ValueError: if the `node_type` is invalid
        """
        try:
            return t.cast(NodeType, load_node_class(node_type))
        except (exceptions.DbContentError, exceptions.MissingEntryPointError) as exception:
            raise EntryPointError(f'invalid node type `{node_type}`') from exception

    def _load_entry_point_from_full_type(self, full_type: str) -> t.Any:
        """Return the loaded entry point for the given `full_type` unique node type identifier.

        :param full_type: the `full_type` unique node type identifier
        :type full_type: str
        :return: the loaded entry point
        :rtype: t.Any
        :raises ValueError: if the `full_type` is invalid
        :raises TypeError: if the `full_type` is not a string type
        :raises `~aiida.common.exceptions.EntryPointError`: if the corresponding entry point cannot be loaded
        """

        data_prefix = 'data.'

        self._validate_full_type(full_type)

        node_type, process_type = full_type.split(self.FULL_TYPE_CONCATENATOR)

        if is_valid_entry_point_string(process_type):
            try:
                return load_entry_point_from_string(process_type)
            except EntryPointError:
                raise EntryPointError(f'could not load entry point `{process_type}`')

        elif node_type.startswith(data_prefix):
            base_name = node_type.removeprefix(data_prefix)
            entry_point_name = base_name.rsplit('.', 2)[0]

            try:
                return load_entry_point('aiida.data', entry_point_name)
            except EntryPointError:
                raise EntryPointError(f'could not load entry point `{process_type}`')

        # Here we are dealing with a `ProcessNode` with a `process_type` that is not an entry point string.
        # Which means it is most likely a full module path (the fallback option) and we cannot necessarily load the
        # class from this. We could try with `importlib` but not sure that we should
        raise EntryPointError('entry point of the given full type cannot be loaded')
