"""REST API models for ORM nodes."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida import orm
from aiida.plugins import get_entry_points
from importlib_metadata import EntryPoint


class NodeModelRegistry:
    """Registry for AiiDA REST API node models.

    This class maintains mappings of node types and their corresponding Pydantic models.

    :ivar ModelUnion: A union type of all AiiDA node Pydantic models, discriminated by the `node_type` field.
    """

    def __init__(self) -> None:
        self.build_node_mappings()
        self.ModelUnion = t.Annotated[
            t.Union[tuple(self._models.values())],
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
        return node_type.rsplit('.', 1)[-1]

    def get_models(self) -> list[type[orm.Node.Model]]:
        """Get the list of registered Pydantic model classes.

        :return: List of Pydantic model classes.
        """
        return list(self._models.values())

    def get_model(self, node_type: str) -> type[orm.Node.Model]:
        """Get the Pydantic model class for a given node type.

        :param node_type: The AiiDA node type string.
        :return: The corresponding Pydantic model class.
        """
        if (Model := self._models.get(node_type)) is None:
            raise KeyError(f'Unknown node type: {node_type}')
        return Model

    def get_node_post_model(self, node_cls: orm.Node, node_type: str) -> type[orm.Node.Model]:
        """Return a patched Model for the given node class with a literal `node_type` field.

        :param node_cls: The AiiDA node class.
        :param node_type: The AiiDA node type string.
        :return: The patched ORM Node model.
        """
        Model = node_cls.CreateModel
        # Here we patch in the `node_type` union descriminator field.
        # We annotate it with `SkipJsonSchema` to keep it off the public openAPI schema.
        Model.model_fields['node_type'] = pdt.fields.FieldInfo(
            annotation=pdt.json_schema.SkipJsonSchema[t.Literal[node_type]],  # type: ignore[misc,valid-type]
            default=node_type,
        )
        return t.cast(type[orm.Node.Model], Model)

    def build_node_mappings(self) -> None:
        """Build mapping of node type to node creation model."""
        self._models: dict[str, type[orm.Node.Model]] = {}
        entry_point: EntryPoint
        for entry_point in get_entry_points('aiida.data') + get_entry_points('aiida.node'):
            try:
                node_cls = t.cast(orm.Node, entry_point.load())
            except Exception as exception:
                # Skip entry points that cannot be loaded
                print(f'Warning: could not load entry point {entry_point.name}: {exception}')
                continue
            node_type = node_cls._plugin_type_string[:-1]
            self._models[node_type] = self.get_node_post_model(node_cls, node_type)
