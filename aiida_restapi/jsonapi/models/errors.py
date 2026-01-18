"""JSON:API error models."""

from __future__ import annotations

import typing as t

import pydantic as pdt

from aiida_restapi.jsonapi.models.base import Error, JsonApiErrorDocument


class JsonDecodingErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['400']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Malformed JSON string']),
    ] = None


class JsonDecodingError(JsonApiErrorDocument[JsonDecodingErrorType]):
    pass


class StoringNotAllowedErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['403']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Resource cannot be stored']),
    ] = None


class StoringNotAllowedError(JsonApiErrorDocument[StoringNotAllowedErrorType]):
    pass


class NonExistentErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['404']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['No result was found']),
    ] = None


class NonExistentError(JsonApiErrorDocument[NonExistentErrorType]):
    pass


class MultipleObjectsErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['409']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Multiple results were found']),
    ] = None


class MultipleObjectsError(JsonApiErrorDocument[MultipleObjectsErrorType]):
    pass


class InvalidInputErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['422']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Input value out of range', 'Invalid POST payload']),
    ] = None


class InvalidInputError(JsonApiErrorDocument[InvalidInputErrorType]):
    pass


class InvalidNodeTypeErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['422']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Unknown node type']),
    ] = None


class InvalidNodeTypeError(JsonApiErrorDocument[InvalidNodeTypeErrorType]):
    pass


class InvalidOperationErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['422']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Failed to submit the process']),
    ] = None


class InvalidOperationError(JsonApiErrorDocument[InvalidOperationErrorType]):
    pass


class RequestValidationErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['422']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Invalid query parameter']),
    ] = None


class RequestValidationError(JsonApiErrorDocument[RequestValidationErrorType]):
    pass


class QueryBuilderErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['422']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Invalid `QueryBuilder` query structure']),
    ] = None


class QueryBuilderError(JsonApiErrorDocument[QueryBuilderErrorType]):
    pass


class InvalidLicenseErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['451']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(examples=['Operation not permitted under current license']),
    ] = None


class InvalidLicenseError(JsonApiErrorDocument[InvalidLicenseErrorType]):
    pass


class DaemonErrorType(Error):
    status: t.Annotated[
        str | None,
        pdt.Field(examples=['500']),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(
            examples=[
                'The daemon is not running',
                'Failed to start daemon',
                'The daemon is already running',
            ]
        ),
    ] = None


class DaemonError(JsonApiErrorDocument[DaemonErrorType]):
    pass
