"""JSON:API utilities."""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from aiida_restapi.jsonapi.models.base import JsonApiErrorDocument

CacheBucket = dict[str, tuple[t.Union[str, int], str, dict[str, t.Any], dict[str, t.Any]]]


@dataclass
class IncludedItemParamsCache:
    """Per-request cache for the parameter of an included resources.

    The cache is used to avoid recomputing the parameters of shared included resources (user, computer, etc.).
    The cache is organized in buckets per resource type and maps to id: (id, type, attributes, foreign fields).
    """

    buckets: dict[str, CacheBucket] = field(default_factory=dict)

    def bucket(self, resource_type: str) -> CacheBucket:
        """Get the cache bucket for a given resource type.

        :param resource_type: The resource type.
        :type resource_type: str
        :return: The cache bucket for the resource type.
        :rtype: CacheBucket
        """
        try:
            return self.buckets[resource_type]
        except KeyError:
            bucket: CacheBucket = {}
            self.buckets[resource_type] = bucket
            return bucket


def jsonapi_error(
    request: Request,
    exception: Exception,
    status_code: int,
) -> JSONResponse:
    """Generate a JSON:API compliant error response.

    :param request: The incoming request.
    :type request: Request
    :param exception: The exception that was raised.
    :type exception: Exception
    :param status_code: The HTTP status code for the response.
    :type status_code: int
    :return: A JSON response containing the error in JSON:API format.
    :rtype: JSONResponse
    """
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            obj=JsonApiErrorDocument(
                links={
                    'self': str(request.url),
                },
                errors=[
                    {
                        'title': exception.__class__.__name__,
                        'status': str(status_code),
                        'detail': str(exception),
                    },
                ],
            ),
            exclude_none=True,
        ),
    )
