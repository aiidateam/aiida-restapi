"""Pydantic models for AiiDA REST API nodes."""

from __future__ import annotations

import typing as t
from importlib.metadata import EntryPoint

import pydantic as pdt
from aiida.common.exceptions import MissingEntryPointError, UnsupportedSchemaError
from aiida.orm import Node, OrmModel
from aiida.plugins import get_entry_points


class NodeStatistics(pdt.BaseModel):
    """Pydantic model representing node statistics."""

    total: int = pdt.Field(
        description='Total number of nodes.',
        examples=[47],
    )
    types: dict[str, int] = pdt.Field(
        description='Number of nodes by type.',
        examples=[
            {
                'data.core.int.Int.': 42,
                'data.core.singlefile.SinglefileData.': 5,
            }
        ],
    )
    ctime_by_day: dict[str, int] = pdt.Field(
        description='Number of nodes created per day (YYYY-MM-DD).',
        examples=[
            {
                '2012-01-01': 10,
                '2012-01-02': 15,
            }
        ],
    )


class NodeType(pdt.BaseModel):
    """Pydantic model representing a node type."""

    label: str = pdt.Field(
        description='The class name of the node type.',
        examples=['Int'],
    )
    node_type: str = pdt.Field(
        description='The AiiDA node type string.',
        examples=['data.core.int.Int.'],
    )
    nodes: str = pdt.Field(
        description='The URL to access nodes of this type.',
        examples=['../nodes?filters={"node_type":{"data.core.int.Int."}}'],
    )
    projections: str = pdt.Field(
        description='The URL to access projectable properties of this node type.',
        examples=['../nodes/projections?type=data.core.int.Int.'],
    )
    node_schema: str = pdt.Field(
        description='The URL to access the schema of this node type.',
        examples=['../nodes/schema?type=data.core.int.Int.'],
    )


class RepoFileMetadata(pdt.BaseModel):
    """Pydantic model representing the metadata of a file in the AiiDA repository."""

    file_type: t.Literal['FILE'] = pdt.Field(
        alias='type',
        description='The type of the repository object.',
        examples=['FILE'],
    )
    binary: bool = pdt.Field(
        False,
        description='Whether the file is binary.',
        examples=[True],
    )
    size: int = pdt.Field(
        description='The size of the file in bytes.',
        examples=[1024],
    )
    file_hash: str = pdt.Field(
        description='The hash of the file in the repository.',
        alias='hash',
    )
    download: str = pdt.Field(
        description='The URL to download the file.',
        examples=['../nodes/{uuid}/repo/contents?filename=path/to/file.txt'],
    )


class RepoDirMetadata(pdt.BaseModel):
    """Pydantic model representing the metadata of a directory in the AiiDA repository."""

    file_type: t.Literal['DIRECTORY'] = pdt.Field(
        alias='type',
        description='The type of the repository object.',
        examples=['DIRECTORY'],
    )
    objects: dict[str, t.Union[RepoFileMetadata, 'RepoDirMetadata']] = pdt.Field(
        description='A dictionary with the metadata of the objects in the directory.',
        examples=[
            {
                'file.txt': {
                    'type': 'FILE',
                    'binary': False,
                    'size': 2048,
                    'download': '../nodes/{uuid}/repo/contents?filename=path/to/file.txt',
                },
                'subdir': {
                    'type': 'DIRECTORY',
                    'objects': {},
                },
            }
        ],
    )


MetadataType = t.Union[RepoFileMetadata, RepoDirMetadata]


class NodeLink(pdt.BaseModel):
    id: str = pdt.Field(
        description='The unique identifier of the link.',
        examples=['<source_uuid>:<target_uuid>'],
    )
    source: str = pdt.Field(
        description='The UUID of the source node.',
        examples=['<source_uuid>'],
    )
    target: str = pdt.Field(
        description='The UUID of the target node.',
        examples=['<target_uuid>'],
    )
    link_label: str = pdt.Field(
        description='The label of the link to the node.',
        examples=['structure'],
    )
    link_type: str = pdt.Field(
        description='The type of the link to the node.',
        examples=['input_calc'],
    )


class NodeModelRegistry:
    """Registry for AiiDA REST API node models.

    This class maintains mappings of node types and their corresponding Pydantic models.

    :ivar WriteModelUnion: An AiiDA ORM model union for attributes-based node creation.
    :ivar ConstructorModelUnion: An AiiDA ORM model union for constructor-based node creation.
    """

    def __init__(self) -> None:
        self._build_node_mappings()
        self.WriteModelUnion = self._build_model_union('write')
        self.ConstructorModelUnion = self._build_model_union('constructor')

    def get_node_types(self) -> list[str]:
        """Get the list of registered node types.

        :return: List of node type strings.
        """
        return list(self._models.keys())

    def get_node_class_name(self, node_type: str) -> str:
        """Get the AiiDA node class name for a given node type.

        :param node_type: The AiiDA node type string.
        :type node_type: str
        :return: The corresponding node class name.
        :rtype: str
        """
        return node_type.rsplit('.', 2)[-2]

    def get_model(
        self,
        node_type: str,
        which: t.Literal['read', 'write', 'constructor'] = 'read',
    ) -> type[OrmModel] | None:
        """Get the Pydantic model class for a given node type.

        :param node_type: The AiiDA node type string.
        :type node_type: str
        :return: The corresponding Pydantic model class.
        :rtype: type[OrmModel] | None
        """
        if (model_dict := self._models.get(node_type)) is None:
            raise MissingEntryPointError(f'Unknown node type: {node_type}')
        if which not in model_dict:
            raise KeyError(f'Unknown model type: {which}')
        return model_dict[which]

    def get_post_model_from_payload(
        self,
        payload: dict[str, t.Any],
        which: t.Literal['write', 'constructor'] | None = None,
    ) -> type[OrmModel]:
        """Get the node creation model (`write` or `constructor`) from payload shape.

        The payload is discriminated using:
        1. `node_type`
        2. presence of `attributes` (write) or `args` (constructor)
        """
        node_type = payload.get('node_type')
        if not isinstance(node_type, str):
            raise ValueError("The 'node_type' field is missing in the payload.")

        has_attributes = 'attributes' in payload
        has_args = 'args' in payload

        if has_attributes and has_args:
            raise ValueError("Payload cannot contain both 'attributes' and 'args'.")

        if which is None:
            which = 'constructor' if has_args else 'write'
        elif which == 'constructor' and has_attributes:
            raise ValueError("Payload cannot contain 'attributes' on the constructor endpoint.")
        elif which == 'write' and has_args:
            raise ValueError("Payload cannot contain 'args' on the attributes endpoint.")

        Model = self.get_model(node_type, which)  # type: ignore[arg-type]
        if Model is None:
            if which == 'constructor':
                raise UnsupportedSchemaError(f"'{node_type}' does not support constructor payloads (`args`).")
            raise ValueError(f"'{node_type}' does not support {which} schema")
        return Model

    def _build_node_mappings(self) -> None:
        """Build mapping of node type to node creation model."""
        self._models: dict[str, dict[str, type[OrmModel] | None]] = {}
        entry_point: EntryPoint
        for entry_point in get_entry_points('aiida.data') + get_entry_points('aiida.node'):
            if entry_point.name == 'data':
                # The root `Data` node type is incompatible with model-based creation
                continue
            try:
                node_cls = t.cast(type[Node], entry_point.load())
            except Exception as exception:
                # Skip entry points that cannot be loaded
                print(f'Warning: could not load entry point {entry_point.name}: {exception}')
                continue

            self._models[node_cls.class_node_type] = {
                'read': node_cls.ReadModel,
                'write': node_cls.WriteModel,
                'constructor': node_cls.ConstructorModel if node_cls.supports_constructor_model else None,
            }

    def _build_model_union(self, which: t.Literal['write', 'constructor']) -> t.Any:
        """Build a union type of node models for the given payload kind."""
        models: list[type[OrmModel]] = []

        excluded_types = {'data.core.code.Code.', 'data.core.code.abstract.AbstractCode.'}
        for node_type, model_dict in self._models.items():
            if node_type.startswith('process') or node_type in excluded_types:
                # These do not support direct creation
                continue
            model = model_dict[which]
            if model is not None:
                models.append(model)

        return t.Annotated[
            t.Union[tuple(models)],
            pdt.Field(discriminator='node_type'),
        ]
