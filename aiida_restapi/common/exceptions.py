"""Common exception classes."""


class QueryBuilderException(Exception):
    """Exception raised for errors during QueryBuilder execution."""


class JsonApiException(Exception):
    """Base exception for JSON:API related errors."""
