# -*- coding: utf-8 -*-
"""Test fixtures specific to this package."""
# pylint: disable=too-many-arguments
from datetime import datetime
from typing import Any, Callable, Mapping, MutableMapping, Optional, Union

import pytest
import pytz
from aiida import orm
from aiida.common.exceptions import NotExistent


def mutate_mapping(
    mapping: Union[MutableMapping, list],
    mutations: Optional[Mapping[str, Callable[[str], Any]]],
):
    """Mutate leaf key values of a potentially nested dict."""
    if isinstance(mapping, list):
        for item in mapping:
            mutate_mapping(item, mutations)
    else:
        for key, item in mapping.items():
            if isinstance(item, (MutableMapping, list)):
                mutate_mapping(item, mutations)
            else:
                if key in mutations:
                    mapping[key] = mutations[key](mapping[key])


@pytest.fixture
def orm_regression(data_regression):
    """A variant of data_regression.check, that replaces nondetermistic fields (like uuid)."""

    def _func(
        data: dict,
        varfields=(
            "id",
            "uuid",
            "time",
            "ctime",
            "mtime",
            "dbnode_id",
            "user_id",
            "_aiida_hash",
        ),
    ):
        mutate_mapping(
            data,
            {key: lambda k: type(k).__name__ for key in varfields},
        )
        if "data" in data:
            # for graphql mutations this is an ordered dict
            data["data"] = dict(data["data"])
        data_regression.check(data)

    return _func


@pytest.fixture
def create_user():
    """Create and store an AiiDA User."""

    def _func(
        email="a@b.com",
        first_name: str = "",
        last_name: str = "",
        institution: str = "",
    ) -> orm.User:
        return orm.User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            institution=institution,
        ).store()

    return _func


@pytest.fixture
def create_comment():
    """Create and store an AiiDA Comment (+ associated user and node)."""

    def _func(
        content: str = "content",
        user_email="verdi@opera.net",
        node: Optional[orm.nodes.Node] = None,
    ) -> orm.Comment:
        try:
            user = orm.User.objects.get(email=user_email)
        except NotExistent:
            user = orm.User(
                email=user_email, first_name="Giuseppe", last_name="Verdi"
            ).store()
        if node is None:
            node = orm.Data()
            node.user = user
            node.store()
        return orm.Comment(node, user, content).store()

    return _func


@pytest.fixture
def create_log():
    """Create and store an AiiDA Log (and node)."""

    def _func(
        loggername: str = "name",
        level_name: str = "level 1",
        message="",
        node: Optional[orm.nodes.Node] = None,
    ) -> orm.Comment:
        orm_node = node or orm.Data().store()
        return orm.Log(
            datetime.now(pytz.UTC), loggername, level_name, orm_node.id, message=message
        ).store()

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


@pytest.fixture
def create_node():
    """Create and store an AiiDA Node."""

    def _func(
        *,
        label: str = "",
        description: str = "",
        attributes: Optional[dict] = None,
        extras: Optional[dict] = None,
        process_type: Optional[str] = None,
        computer: Optional[orm.Computer] = None,
        store: bool = True
    ) -> orm.nodes.Node:
        node = (
            orm.CalcJobNode(computer=computer)
            if process_type
            else orm.Data(computer=computer)
        )
        node.label = label
        node.description = description
        node.reset_attributes(attributes or {})
        node.reset_extras(extras or {})
        if process_type is not None:
            node.process_type = process_type
        if store:
            node.store()
        return node

    return _func


@pytest.fixture
def create_group():
    """Create and store an AiiDA Group."""

    def _func(
        label: str = "group",
        description: str = "",
        type_string: Optional[str] = None,
    ) -> orm.Group:
        return orm.Group(
            label=label,
            description=description,
            type_string=type_string,
        ).store()

    return _func
