# -*- coding: utf-8 -*-
"""Adapted JSON API models.

Adapting pydantic_jsonapi.response to fit the non-compliant AiiDA REST API responses.
Changes made as comments.
"""
# pylint: disable=missing-class-docstring,redefined-builtin,missing-function-docstring,too-few-public-methods
from typing import Generic, Optional, TypeVar, get_type_hints

from pydantic.generics import GenericModel
from pydantic_jsonapi.filter import filter_none
from pydantic_jsonapi.relationships import ResponseRelationshipsType
from pydantic_jsonapi.resource_links import ResourceLinks

# TypeT = TypeVar('TypeT', bound=str)
# AttributesT = TypeVar("AttributesT")


# class ResponseDataModel(GenericModel):

#     id: str
#     relationships: Optional[ResponseRelationshipsType]
#     links: Optional[ResourceLinks]

#     class Config:
#         validate_all = True
#         extra = "allow"  # added


DataT = TypeVar("DataT")  # , bound=ResponseDataModel)


class ResponseModel(GenericModel, Generic[DataT]):

    data: DataT
    included: Optional[list]
    meta: Optional[dict]
    links: Optional[ResourceLinks]

    def dict(self, *, serlialize_none: bool = False, **kwargs):
        response = super().dict(**kwargs)
        if serlialize_none:
            return response
        return filter_none(response)

    @classmethod
    def resource_object(
        cls,
        *,
        id: str,
        attributes: Optional[dict] = None,
        relationships: Optional[dict] = None,
        links: Optional[dict] = None,
    ) -> DataT:
        data_type = get_type_hints(cls)["data"]
        if getattr(data_type, "__origin__", None) is list:
            data_type = data_type.__args__[0]
        typename = get_type_hints(data_type)["type"].__args__[0]
        return data_type(
            id=id,
            type=typename,
            attributes=attributes or {},
            relationships=relationships,
            links=links,
        )
