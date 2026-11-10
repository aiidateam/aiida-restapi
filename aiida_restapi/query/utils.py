"""General utilities shared by query parameter modules."""

from __future__ import annotations


def parse_csv(raw: str) -> list[str]:
    """Split comma-separated values, trimming whitespace and dropping empty items.

    :param raw: The comma-separated input string.
    :return: Non-empty trimmed values.
    :rtype: list[str]
    """
    return [item.strip() for item in raw.split(',') if item.strip()]
