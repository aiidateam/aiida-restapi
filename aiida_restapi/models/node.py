"""Pydantic models for AiiDA REST API nodes."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida.common.exceptions import MissingEntryPointError
from aiida.common.pydantic import OrmModel
from aiida.orm import Node
from aiida.plugins import get_entry_points
from importlib_metadata import EntryPoint


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

    :ivar ModelUnion: A union type of all AiiDA node Pydantic models, discriminated by the `node_type|write_mode`
        composite field.
    """

    def __init__(self) -> None:
        self._build_node_mappings()
        self.ModelUnion = self._build_model_union()

    def get_node_types(self) -> list[str]:
        """Get the list of registered node class names.

        :return: List of node class names.
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
    ) -> type[OrmModel]:
        """Get the Pydantic model class for a given node type.

        :param node_type: The AiiDA node type string.
        :type node_type: str
        :return: The corresponding Pydantic model class.
        :rtype: type[OrmModel]
        """
        if (Model := self._models.get(node_type)) is None:
            raise MissingEntryPointError(f'Unknown node type: {node_type}')
        if which not in Model:
            raise KeyError(f'Unknown model type: {which}')
        return Model[which]

    def _get_node_post_models(self, node_cls: Node) -> dict[str, type[OrmModel]]:
        """Get the 'write' and 'constructor' Pydantic models for a given AiiDA node class.

        :param node_cls: The AiiDA node class.
        :type node_cls: Node
        :return: The ORM Node models for post and optional constructor creation.
        :rtype: type[Node.OrmModel]
        """
        models: dict[str, type[OrmModel]] = {'write': node_cls.WriteModel}
        if node_cls.ConstructorModel is not None:
            models['constructor'] = node_cls.ConstructorModel
        return models

    def _build_node_mappings(self) -> None:
        """Build mapping of node type to node creation model."""
        self._models: dict[str, dict[str, type[OrmModel]]] = {}
        entry_point: EntryPoint
        for entry_point in get_entry_points('aiida.data') + get_entry_points('aiida.node'):
            try:
                node_cls = t.cast(Node, entry_point.load())
            except Exception as exception:
                # Skip entry points that cannot be loaded
                print(f'Warning: could not load entry point {entry_point.name}: {exception}')
                continue

            self._models[node_cls.class_node_type] = {
                'read': node_cls.ReadModel,
                **self._get_node_post_models(node_cls),
            }

    def _get_post_models(self) -> tuple[type[OrmModel], ...]:
        """Get a union type of all node 'write' models.

        :return: A union type of all node 'write' models.
        :rtype: tuple[type[OrmModel], ...]
        """
        models: list[type[OrmModel]] = []

        for model_dict in self._models.values():
            models.append(model_dict['write'])
            if 'constructor' in model_dict:
                models.append(model_dict['constructor'])

        return tuple(models)

    def _build_model_union(self):
        """Build a union type of all node models.

        The union uses a nested discriminator:
        - outer: `node_type`
        - inner: `write_mode` ('attributes' or 'constructor')
        """

        tagged_models: list[object] = []

        for node_type, model_dict in self._models.items():
            write_model = model_dict['write']
            tagged_models.append(t.Annotated[write_model, pdt.Tag(f'{node_type}|attributes')])

            if 'constructor' in model_dict:
                constructor_model = model_dict['constructor']
                tagged_models.append(
                    t.Annotated[
                        constructor_model,
                        pdt.Tag(f'{node_type}|constructor'),
                    ]
                )

        def discriminator(value):
            if isinstance(value, dict):
                return f'{value.get("node_type")}|{value.get("write_mode")}'
            return f'{value.node_type}|{value.write_mode}'

        return t.Annotated[
            t.Union.__getitem__(tuple(tagged_models)),
            pdt.Discriminator(discriminator),
        ]
