"""General utility functions."""

import datetime

from dateutil.parser import parser as date_parser


def parse_date(string: str) -> datetime.datetime:
    """Parse any date/time stamp string."""
    return date_parser().parse(string)
