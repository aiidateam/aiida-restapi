from __future__ import annotations

import pydantic as pdt
from aiida import orm
from aiida.common.pydantic import get_metadata

from .base import Attributes, JsonApiCollectionDocument, JsonApiResourceDocument, Resource


def attributes_of(orm_class: type[orm.Entity]) -> type[Attributes]:
    """Dynamically derive Attributes class for a given AiiDA ORM class."""

    fields = {}
    for key, field in orm_class.Model.model_fields.items():
        if key == orm_class.identity_field:
            continue
        if get_metadata(field, 'may_be_large') or get_metadata(field, 'write_only'):
            continue
        try:
            orm.entities.EntityTypes(key)
        except ValueError:
            fields[key] = (field.annotation, field)

    return pdt.create_model(
        f'{orm_class.__name__}Attributes',
        __base__=Attributes,
        **fields,  # type: ignore[call-overload]
    )


UserAttributes = attributes_of(orm.User)
UserResource = Resource[UserAttributes]  # type: ignore[valid-type]
UserResourceDocument = JsonApiResourceDocument[UserResource]
UserCollectionDocument = JsonApiCollectionDocument[UserResource]

ComputerAttributes = attributes_of(orm.Computer)
ComputerResource = Resource[ComputerAttributes]  # type: ignore[valid-type]
ComputerResourceDocument = JsonApiResourceDocument[ComputerResource]
ComputerCollectionDocument = JsonApiCollectionDocument[ComputerResource]

GroupAttributes = attributes_of(orm.Group)
GroupResource = Resource[GroupAttributes]  # type: ignore[valid-type]
GroupResourceDocument = JsonApiResourceDocument[GroupResource]
GroupCollectionDocument = JsonApiCollectionDocument[GroupResource]

NodeAttributes = attributes_of(orm.Node)
NodeResource = Resource[NodeAttributes]  # type: ignore[valid-type]
NodeResourceDocument = JsonApiResourceDocument[NodeResource]
NodeCollectionDocument = JsonApiCollectionDocument[NodeResource]


class LinkAttributes(Attributes):
    """Link attributes."""

    link_label: str = pdt.Field(
        description='The label of the link to the node.',
        examples=['structure'],
    )
    link_type: str = pdt.Field(
        description='The type of the link to the node.',
        examples=['input_calc'],
    )


LinkResource = Resource[LinkAttributes]
LinkCollectionDocument = JsonApiCollectionDocument[LinkResource]
