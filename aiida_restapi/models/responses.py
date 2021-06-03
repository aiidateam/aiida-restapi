# -*- coding: utf-8 -*-
"""Response schemas for AiiDA REST API.

Builds upon response schemas from `json_api` module.
"""

from typing import List, Type, TypeVar

from pydantic_jsonapi import ErrorResponse

from . import json_api
from .entities import AiidaModel  # pylint: disable=unused-import

__all__ = ("EntityResponse", "ErrorResponse")

ModelType = TypeVar("ModelType", bound="AiidaModel")


def EntityResponse(
    # type_string: str,
    attributes_model: ModelType,
    *,
    use_list: bool = False,
) -> Type[json_api.ResponseModel]:
    """Returns entity-specif pydantic response model."""
    response_data_model = attributes_model
    type_string = (
        attributes_model._orm_entity.__name__.lower()  # pylint: disable=protected-access
    )
    if use_list:
        response_data_model.__name__ = f"ListResponseData[{type_string}]"
        response_model = json_api.ResponseModel[List[response_data_model]]
        response_model.__name__ = f"ListResponse[{type_string}]"
    else:
        response_data_model.__name__ = f"ResponseData[{type_string}]"
        response_model = json_api.ResponseModel[response_data_model]
        response_model.__name__ = f"Response[{type_string}]"
    return response_model
