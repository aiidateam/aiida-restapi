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
            pdt.Field(discriminator='orm_class'),
        ]

    def get_node_types(self) -> list[str]:
        """Get the list of registered node class names.

        :return: List of node class names.
        """
        return list(self._types.keys())

    def get_node_type(self, node_class: str) -> str:
        """Get the node type string for a given node class name.

        :param node_class: The name of the AiiDA node class.
        :return: The corresponding node type string.
        """
        if (node_type := self._types.get(node_class)) is None:
            raise KeyError(f'Unknown node class: {node_class}')
        return node_type

    def get_models(self) -> list[type[orm.Node.Model]]:
        """Get the list of registered Pydantic model classes.

        :return: List of Pydantic model classes.
        """
        return list(self._models.values())

    def get_model(self, node_class: str) -> type[orm.Node.Model]:
        """Get the Pydantic model class for a given node type.

        :param node_class: The name of the AiiDA node class.
        :return: The corresponding Pydantic model class.
        """
        if (Model := self._models.get(node_class)) is None:
            raise KeyError(f'Unknown node class: {node_class}')
        return Model

    def get_node_post_model(self, node_cls: orm.Node) -> type[orm.Node.Model]:
        """Return a patched Model for the given node class with a literal `orm_class` field.

        :param node_cls: The AiiDA node class.
        :return: The patched ORM Node model.
        """
        Model = node_cls.InputModel
        # Here we patch in the `orm_class` union descriminator field.
        # We annotate it with `SkipJsonSchema` to keep it off the public openAPI schema.
        Model.model_fields['orm_class'] = pdt.fields.FieldInfo(
            annotation=pdt.json_schema.SkipJsonSchema[t.Literal[node_cls.__name__]],  # type: ignore[misc,valid-type]
            default=node_cls.__name__,
        )
        return t.cast(type[orm.Node.Model], Model)

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
            models[node_cls_name] = self.get_node_post_model(node_cls)
        return types, models
