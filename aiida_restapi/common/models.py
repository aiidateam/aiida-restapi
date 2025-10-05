"""REST API model utilities."""

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
        self._types: dict[str, str] = {}
        self._models: dict[str, type[orm.Node.Model]] = {}
        self._types, self._models = self.build_node_mappings()
        self.ModelUnion = t.Annotated[
            t.Union[tuple(self._models.values())],
            pdt.Field(discriminator='node_type'),
        ]

    def get_node_types(self) -> list[str]:
        """Get the list of registered node class names.

        :return: List of node class names.
        """
        return list(self._types.keys())

    def get_node_type(self, node_class_name: str) -> str | None:
        """Get the node type string for a given node class name.

        :param node_class_name: The name of the AiiDA node class.
        :return: The corresponding node type string.
        """
        return self._types.get(node_class_name)

    def get_model(self, node_class_name: str) -> type[orm.Node.Model] | None:
        """Get the Pydantic model class for a given node type.

        :param node_class_name: The name of the AiiDA node class.
        :return: The corresponding Pydantic model class.
        """
        return self._models.get(node_class_name, None)

    def literalize_node_model(self, node_cls: orm.Node, node_type: str) -> type[orm.Node.Model]:
        """Extend the given node class's model with a literal node type field.

        :param node_cls: The AiiDA node class.
        :param node_type: The node type name of the node class.
        :return: The extended Pydantic model class.
        """
        return pdt.create_model(
            f'{node_cls.__name__}RestModel',
            __base__=node_cls.Model,
            node_type=(t.Literal[node_type], node_type),
        )

    def build_node_mappings(self) -> tuple[dict[str, str], dict[str, type[orm.Node.Model]]]:
        """Build node mappings to node types and node models.

        :return: A tuple of (types, models) where `types` is a mapping of node class names to node type strings,
                and `models` is a mapping of node class names to their corresponding Pydantic model classes.
        """
        types: dict[str, str] = {}
        models: dict[str, type[orm.Node.Model]] = {}
        entry_point: EntryPoint
        for entry_point in get_entry_points('aiida.data') + get_entry_points('aiida.node'):
            try:
                node_cls = t.cast(orm.Node, entry_point.load())
            except Exception as exception:
                # Skip entry points that cannot be loaded
                print(f'Warning: could not load entry point {entry_point.name}: {exception}')
                continue
            node_type = node_cls._plugin_type_string
            node_cls_name = node_cls.__name__
            if node_cls_name in models:
                continue
            types[node_cls_name] = node_type
            models[node_cls_name] = self.literalize_node_model(node_cls, node_type)
        return types, models
