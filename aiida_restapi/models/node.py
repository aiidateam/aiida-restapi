"""Pydantic models for AiiDA REST API nodes."""

from __future__ import annotations

import typing as t
from copy import deepcopy

import pydantic as pdt
from aiida.common.exceptions import MissingEntryPointError
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
        which: t.Literal['get', 'post', 'constructor'] = 'get',
    ) -> type[Node.BaseWriteModel]:
        """Get the Pydantic model class for a given node type.

        :param node_type: The AiiDA node type string.
        :type node_type: str
        :return: The corresponding Pydantic model class.
        :rtype: type[Node.BaseWriteModel]
        """
        if (Model := self._models.get(node_type)) is None:
            raise MissingEntryPointError(f'Unknown node type: {node_type}')
        if which not in Model:
            raise KeyError(f'Unknown model type: {which}')
        return Model[which]

    def _patch_discriminator_fields(
        self,
        Model: type[Node.BaseWriteModel],
        *,
        node_type: str,
        write_mode: t.Literal['post', 'constructor'],
    ) -> type[Node.BaseWriteModel]:
        """Patch discriminator fields onto a model.

        Assumes the model class is already subclass-local, i.e. safe to mutate.
        """
        Model.model_fields['node_type'] = pdt.fields.FieldInfo(
            annotation=pdt.json_schema.SkipJsonSchema[t.Literal[node_type]],
            default=node_type,
        )
        Model.model_fields['write_mode'] = pdt.fields.FieldInfo(
            annotation=pdt.json_schema.SkipJsonSchema[t.Literal[write_mode]],
            default=write_mode,
        )
        Model.model_rebuild(force=True)
        return Model

    def _get_node_post_models(self, node_cls: Node) -> dict[str, type[Node.BaseWriteModel]]:
        """Get the 'post' and 'constructor' Pydantic models for a given AiiDA node class.

        :param node_cls: The AiiDA node class.
        :type node_cls: Node
        :return: The patched ORM Node model.
        :rtype: type[Node.BaseWriteModel]
        """
        node_type = node_cls.class_node_type
        models: dict[str, type[Node.BaseWriteModel]] = {}

        def clone_model_class(Model: type[Node.BaseWriteModel]) -> type[Node.BaseWriteModel]:
            field_definitions: dict[str, tuple[t.Any, t.Any]] = {}
            for field_name, field_info in Model.model_fields.items():
                field_definitions[field_name] = (field_info.annotation, deepcopy(field_info))

            Clone = t.cast(
                type[Node.BaseWriteModel],
                pdt.create_model(
                    f'{Model.__name__}Discriminated',
                    __module__=Model.__module__,
                    __base__=pdt.BaseModel,
                    **field_definitions,
                ),  # type: ignore[call-arg]
            )
            Clone.model_config['extra'] = Model.model_config.get('extra', 'ignore')
            Clone.model_config['title'] = Model.model_config.get('title', Model.__qualname__.replace('.', ''))
            return Clone

        WriteModel = self._patch_discriminator_fields(
            clone_model_class(node_cls.WriteModel),
            node_type=node_type,
            write_mode='post',
        )
        models['post'] = WriteModel

        if node_cls.ConstructorModel is not None:
            ConstructorModel = self._patch_discriminator_fields(
                clone_model_class(node_cls.ConstructorModel),
                node_type=node_type,
                write_mode='constructor',
            )
            models['constructor'] = ConstructorModel

        return models

    def _build_node_mappings(self) -> None:
        """Build mapping of node type to node creation model."""
        self._models: dict[str, dict[str, type[Node.BaseWriteModel]]] = {}
        entry_point: EntryPoint
        for entry_point in get_entry_points('aiida.data') + get_entry_points('aiida.node'):
            try:
                node_cls = t.cast(Node, entry_point.load())
            except Exception as exception:
                # Skip entry points that cannot be loaded
                print(f'Warning: could not load entry point {entry_point.name}: {exception}')
                continue

            self._models[node_cls.class_node_type] = {
                'get': node_cls.ReadModel,
                **self._get_node_post_models(node_cls),
            }

    def _get_post_models(self) -> tuple[type[Node.BaseWriteModel], ...]:
        """Get a union type of all node 'post' models.

        :return: A union type of all node 'post' models.
        :rtype: tuple[type[Node.BaseWriteModel], ...]
        """
        models: list[type[Node.BaseWriteModel]] = []

        for model_dict in self._models.values():
            models.append(model_dict['post'])
            if 'constructor' in model_dict:
                models.append(model_dict['constructor'])

        return tuple(models)

    def _build_model_union(self):
        """Build a union type of all node models.

        The union uses a nested discriminator:
        - outer: `node_type`
        - inner: `write_mode` (post or constructor)
        """

        tagged_models: list[object] = []

        for node_type, model_dict in self._models.items():
            post_model = model_dict['post']
            tagged_models.append(
                t.Annotated[
                    post_model,
                    pdt.Tag(f'{node_type}|post'),
                ]
            )

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
