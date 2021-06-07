# -*- coding: utf-8 -*-
"""Test fixtures specific to this package."""
# pylint: disable=too-many-arguments
from typing import Any, Callable, Mapping, MutableMapping, Optional

import pytest
from aiida import orm


def mutate_mapping(
    mapping: MutableMapping, mutations: Optional[Mapping[str, Callable[[str], Any]]]
):
    """Mutate leaf key values of a potentially nested dict."""
    for key, item in mapping.items():
        if isinstance(item, MutableMapping):
            mutate_mapping(item, mutations)
        else:
            if key in mutations:
                mapping[key] = mutations[key](mapping[key])


@pytest.fixture
def orm_regression(data_regression):
    """A variant of data_regression.check, that replaces nondetermistic fields (like uuid)."""

    def _func(
        data: dict, varfields=("id", "uuid", "ctime", "mtime", "dbnode_id", "user_id")
    ):
        mutate_mapping(
            data,
            {key: lambda k: type(k).__name__ for key in varfields},
        )
        data_regression.check(data)

    return _func


@pytest.fixture
def create_comment():
    """Create and store an AiiDA Comment (and the user and node)."""

    def _func(content: str = "content") -> orm.Comment:
        orm_user = orm.User(
            email="verdi@opera.net", first_name="Giuseppe", last_name="Verdi"
        ).store()
        orm_node = orm.Data().store()
        return orm.Comment(orm_node, orm_user, content).store()

    return _func


@pytest.fixture
def create_computer():
    """Create and store an AiiDA Computer."""

    def _func(
        label: str = "localhost",
        hostname: str = "localhost",
        transport_type: str = "local",
        scheduler_type: str = "direct",
        description: str = "",
        workdir: Optional[str] = None,
    ) -> orm.Computer:
        return orm.Computer(
            label=label,
            description=description,
            hostname=hostname,
            workdir=workdir,
            transport_type=transport_type,
            scheduler_type=scheduler_type,
        ).store()

    return _func
