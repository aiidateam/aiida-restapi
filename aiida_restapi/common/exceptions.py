"""Common exception classes."""


class QueryBuilderException(Exception):
    """Exception raised for errors during QueryBuilder execution."""


class JsonApiException(Exception):
    """Base exception for JSON:API related errors."""


class SchemaNotSupported(Exception):
    """Exception raised when a node type does not support a particular schema type."""


class UnsupportedConstructorModel(Exception):
    """Exception raised when a constructor payload is used for a node type without constructor support."""

    def __init__(self, node_type: str) -> None:
        super().__init__(
            f"'{node_type}' does not support constructor payloads (`args`). "
            'Use an `attributes` payload or select a node type with constructor support.'
        )
