from __future__ import annotations

import typing as t

import pydantic as pdt
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

    label: str = pdt.Field(description='The class name of the node type.')
    node_type: str = pdt.Field(description='The AiiDA node type string.')
    nodes: str = pdt.Field(description='The URL to access nodes of this type.')
    projections: str = pdt.Field(description='The URL to access projectable properties of this node type.')
    node_schema: str = pdt.Field(description='The URL to access the schema of this node type.')


class RepoFileMetadata(pdt.BaseModel):
    """Pydantic model representing the metadata of a file in the AiiDA repository."""

    type: t.Literal['FILE'] = pdt.Field(
        description='The type of the repository object.',
    )
    binary: bool = pdt.Field(
        False,
        description='Whether the file is binary.',
    )
    size: int = pdt.Field(
        description='The size of the file in bytes.',
    )
    download: str = pdt.Field(
        description='The URL to download the file.',
    )


class RepoDirMetadata(pdt.BaseModel):
    """Pydantic model representing the metadata of a directory in the AiiDA repository."""

    type: t.Literal['DIRECTORY'] = pdt.Field(
        description='The type of the repository object.',
    )
    objects: dict[str, t.Union[RepoFileMetadata, 'RepoDirMetadata']] = pdt.Field(
        description='A dictionary with the metadata of the objects in the directory.',
    )


MetadataType = t.Union[RepoFileMetadata, RepoDirMetadata]


class NodeLink(Node.Model):
    link_label: str = pdt.Field(description='The label of the link to the node.')
    link_type: str = pdt.Field(description='The type of the link to the node.')


class NodeModelRegistry:
    """Registry for AiiDA REST API node models.

    This class maintains mappings of node types and their corresponding Pydantic models.

    :ivar ModelUnion: A union type of all AiiDA node Pydantic models, discriminated by the `node_type` field.
    """

    def __init__(self) -> None:
        self._build_node_mappings()
        self.ModelUnion = t.Annotated[
            t.Union[self._get_post_models()],
            pdt.Field(discriminator='node_type'),
        ]

    def get_node_types(self) -> list[str]:
        """Get the list of registered node class names.

        :return: List of node class names.
        """
        return list(self._models.keys())

    def get_node_class_name(self, node_type: str) -> str:
        """Get the AiiDA node class name for a given node type.

        :param node_type: The AiiDA node type string.
        :return: The corresponding node class name.
        """
        return node_type.rsplit('.', 2)[-2]

    def get_model(self, node_type: str, which: t.Literal['get', 'post'] = 'get') -> type[Node.Model]:
        """Get the Pydantic model class for a given node type.

        :param node_type: The AiiDA node type string.
        :return: The corresponding Pydantic model class.
        """
        if (Model := self._models.get(node_type)) is None:
            raise KeyError(f'Unknown node type: {node_type}')
        if which not in Model:
            raise KeyError(f'Unknown model type: {which}')
        return Model[which]

    def _get_node_post_model(self, node_cls: Node) -> type[Node.Model]:
        """Return a patched Model for the given node class with a literal `node_type` field.

        :param node_cls: The AiiDA node class.
        :return: The patched ORM Node model.
        """
        Model = node_cls.CreateModel
        node_type = node_cls.class_node_type
        # Here we patch in the `node_type` union descriminator field.
        # We annotate it with `SkipJsonSchema` to keep it off the public openAPI schema.
        Model.model_fields['node_type'] = pdt.fields.FieldInfo(
            annotation=pdt.json_schema.SkipJsonSchema[t.Literal[node_type]],  # type: ignore[misc,valid-type]
            default=node_type,
        )
        Model.model_rebuild(force=True)
        return t.cast(type[Node.Model], Model)

    def _build_node_mappings(self) -> None:
        """Build mapping of node type to node creation model."""
        self._models: dict[str, dict[str, type[Node.Model]]] = {}
        entry_point: EntryPoint
        for entry_point in get_entry_points('aiida.data'):
            try:
                node_cls = t.cast(Node, entry_point.load())
            except Exception as exception:
                # Skip entry points that cannot be loaded
                print(f'Warning: could not load entry point {entry_point.name}: {exception}')
                continue

            self._models[node_cls.class_node_type] = {
                'get': node_cls.Model,
                'post': self._get_node_post_model(node_cls),
            }

    def _get_post_models(self) -> tuple[type[Node.Model], ...]:
        """Get a union type of all node 'post' models.

        :return: A union type of all node 'post' models.
        """
        post_models = [model_dict['post'] for model_dict in self._models.values()]
        return tuple(post_models)
