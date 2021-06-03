# -*- coding: utf-8 -*-
"""Response schemas for AiiDA REST API.

Builds upon response schemas from `json_api` module.
"""
# pylint: disable=too-few-public-methods

from pydantic import Field
from typing import TypeVar, List, Generic

from pydantic.main import BaseModel

from .entities import AiidaModel
from . import json_api

__all__ = ('Response',)

ModelType = TypeVar("ModelType", bound="AiidaModel")

class _Response(json_api.Response, Generic[ModelType]):
    """Template model for successful REST API responses."""
    data: ModelType = Field(description="List of requested data")

def Response(resource_model: ModelType, use_list: bool = False):
    """Returns response model for specific resource.

    Use e.g. as follows::

        Response(User)
        Response(User, use_list=True)
    
    """
    if use_list:
        resource_model = List[resource_model]

    return _Response[resource_model]


# class ResponseError(Response):
#     """errors MUST be present and data MUST be skipped"""

#     errors: List[json_api.Error] = Field(
#         ...,
#         description="A list of error objects.",
#         uniqueItems=True,
#     )

#     @root_validator(pre=True)
#     def data_must_be_skipped(cls, values):
#         if values.get("data", None) is not None:
#             raise ValueError("data MUST be skipped for failures reporting errors")
#         return values