"""Common exception classes."""


class QueryBuilderException(Exception):
    """Exception raised for errors during QueryBuilder execution."""


class JsonApiException(Exception):
    """Base exception for JSON:API related errors."""


class SchemaNotSupported(Exception):
    """Exception raised when a node type does not support a particular schema type."""


class InvalidRequestError(Exception):
    """Exception raised when request data is invalid for an API endpoint."""
