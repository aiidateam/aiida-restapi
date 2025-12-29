"""Common error models.

These are used in ReDoc and OpenAPI documentation to describe error responses.
"""

import pydantic as pdt


class JsonDecodingError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The provided JSON input is invalid.',
        examples=['Malformed JSON string'],
    )


class NonExistentError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The requested resource does not exist.',
        examples=['No result was found'],
    )


class MultipleObjectsError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='Multiple resources were found when exactly one was expected.',
        examples=['Multiple results were found'],
    )


class StoringNotAllowedError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='Attempt to store the new resource was rejected.',
        examples=['Resource cannot be stored'],
    )


class InvalidInputError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The input provided was invalid.',
        examples=['Input value out of range'],
    )


class InvalidNodeTypeError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The node type does not exist.',
        examples=['Unknown node type: "data.nonexistent.NonExistentNode"'],
    )


class InvalidLicenseError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The operation is not permitted due to licensing restrictions.',
        examples=['Operation not permitted under current license'],
    )


class DaemonError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='An error occurred while interacting with the AiiDA daemon.',
        examples=[
            'The daemon is not running',
            'Failed to start daemon',
            'The daemon is already running',
        ],
    )


class InvalidOperationError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The requested operation is invalid.',
        examples=['Cannot submit a process with `store_provenance=False`'],
    )


class RequestValidationError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='The request parameters failed validation.',
        examples=['Invalid query parameter: "sort"'],
    )


class QueryBuilderError(pdt.BaseModel):
    detail: str = pdt.Field(
        description='An error occurred while processing the QueryBuilder request.',
        examples=['Invalid QueryBuilder query structure'],
    )
