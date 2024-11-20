"""Test fixtures specific to this package."""

# pylint: disable=too-many-arguments
import tempfile
from datetime import datetime
from typing import Any, Callable, Mapping, MutableMapping, Optional, Union

import pytest
import pytz
from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.engine import ProcessState
from aiida.orm import WorkChainNode, WorkFunctionNode
from fastapi.testclient import TestClient
from httpx import AsyncClient

from aiida_restapi import app, config
from aiida_restapi.routers.auth import UserInDB, get_current_user

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


@pytest.fixture(scope='function', autouse=True)
def clear_database_auto(aiida_profile_clean):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""


@pytest.fixture(scope='function')
def client():
    """Return fastapi test client."""
    yield TestClient(app)


@pytest.fixture
def anyio_backend():
    """Return the async IO backend to use for testing.

    Returns:
        str: The name of the backend to use
    """
    return 'asyncio'


@pytest.fixture(scope='function')
async def async_client():
    """Return fastapi async test client."""
    async with AsyncClient(app=app, base_url='http://test') as async_test_client:
        yield async_test_client


@pytest.fixture(scope='function')
def default_users():
    """Populate database with some users."""
    user_1 = orm.User(email='verdi@opera.net', first_name='Giuseppe', last_name='Verdi').store()
    user_2 = orm.User(email='stravinsky@symphony.org', first_name='Igor', last_name='Stravinsky').store()

    return [user_1.pk, user_2.pk]


@pytest.fixture(scope='function')
def default_computers():
    """Populate database with some computer"""
    comp_1 = orm.Computer(
        label='test_comp_1',
        hostname='localhost_1',
        transport_type='core.local',
        scheduler_type='core.pbspro',
    ).store()
    comp_2 = orm.Computer(
        label='test_comp_2',
        hostname='localhost_2',
        transport_type='core.local',
        scheduler_type='core.pbspro',
    ).store()

    return [comp_1.pk, comp_2.pk]


@pytest.fixture(scope='function')
def example_processes():
    """Populate database with some processes"""
    calcs = []
    process_label = 'SomeDummyWorkFunctionNode'

    # Create 6 WorkFunctionNodes and WorkChainNodes (one for each ProcessState)
    for state in ProcessState:
        calc = WorkFunctionNode()
        calc.set_process_state(state)

        # Set the WorkFunctionNode as successful
        if state == ProcessState.FINISHED:
            calc.set_exit_status(0)

        # Give a `process_label` to the `WorkFunctionNodes` so the `--process-label` option can be tested
        calc.base.attributes.set('process_label', process_label)

        calc.store()
        calcs.append(calc.pk)

        calc = WorkChainNode()
        calc.set_process_state(state)

        # Set the WorkChainNode as failed
        if state == ProcessState.FINISHED:
            calc.set_exit_status(1)

        # Set the waiting work chain as paused as well
        if state == ProcessState.WAITING:
            calc.pause()

        calc.store()
        calcs.append(calc.pk)
    return calcs


@pytest.fixture(scope='function')
def default_test_add_process():
    """Populate database with some node to test adding process"""

    workdir = tempfile.mkdtemp()

    computer = orm.Computer(
        label='localhost',
        hostname='localhost',
        workdir=workdir,
        transport_type='core.local',
        scheduler_type='core.direct',
    )
    computer.store()
    computer.set_minimum_job_poll_interval(0.0)
    computer.configure()

    code = orm.InstalledCode(
        default_calc_job_plugin='core.arithmetic.add',
        computer=computer,
        filepath_executable='/bin/true',
    ).store()

    x = orm.Int(1).store()

    y = orm.Int(2).store()

    return [code.uuid, x.uuid, y.uuid]


@pytest.fixture(scope='function')
def default_groups():
    """Populate database with some groups."""
    test_user_1 = orm.User(email='verdi@opera.net', first_name='Giuseppe', last_name='Verdi').store()
    test_user_2 = orm.User(email='stravinsky@symphony.org', first_name='Igor', last_name='Stravinsky').store()
    group_1 = orm.Group(label='test_label_1', user=test_user_1).store()
    group_2 = orm.Group(label='test_label_2', user=test_user_2).store()
    return [group_1.pk, group_2.pk]


@pytest.fixture(scope='function')
def default_nodes():
    """Populate database with some nodes."""
    node_1 = orm.Int(1).store()
    node_2 = orm.Float(1.1).store()
    node_3 = orm.Str('test_string').store()
    node_4 = orm.Bool(False).store()

    return [node_1.pk, node_2.pk, node_3.pk, node_4.pk]


@pytest.fixture(scope='function')
def authenticate():
    """Authenticate user.

    Since this goes via modifying the app, undo modifications afterwards.
    """

    async def logged_in_user(token=None):  # pylint: disable=unused-argument
        """Fake active user."""
        return UserInDB(**config.fake_users_db['johndoe@example.com'])

    app.dependency_overrides[get_current_user] = logged_in_user
    yield
    app.dependency_overrides = {}


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
            elif key in mutations:
                mapping[key] = mutations[key](mapping[key])


@pytest.fixture
def orm_regression(data_regression):
    """A variant of data_regression.check, that replaces nondetermistic fields (like uuid)."""

    def _func(
        data: dict,
        varfields=(
            'id',
            'uuid',
            'time',
            'ctime',
            'mtime',
            'dbnode_id',
            'user_id',
            '_aiida_hash',
            'aiidaVersion',
        ),
    ):
        mutate_mapping(
            data,
            {key: lambda k: type(k).__name__ for key in varfields},
        )
        data_regression.check(data)

    return _func


@pytest.fixture
def create_user():
    """Create and store an AiiDA User."""

    def _func(
        email='a@b.com',
        first_name: str = '',
        last_name: str = '',
        institution: str = '',
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
        content: str = 'content',
        user_email='verdi@opera.net',
        node: Optional[orm.nodes.Node] = None,
    ) -> orm.Comment:
        try:
            user = orm.User.collection.get(email=user_email)
        except NotExistent:
            user = orm.User(email=user_email, first_name='Giuseppe', last_name='Verdi').store()
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
        loggername: str = 'name',
        level_name: str = 'level 1',
        message='',
        node: Optional[orm.nodes.Node] = None,
    ) -> orm.Comment:
        orm_node = node or orm.Data().store()
        return orm.Log(datetime.now(pytz.UTC), loggername, level_name, orm_node.pk, message=message).store()

    return _func


@pytest.fixture
def create_computer():
    """Create and store an AiiDA Computer."""

    def _func(
        label: str = 'localhost',
        hostname: str = 'localhost',
        transport_type: str = 'core.local',
        scheduler_type: str = 'core.direct',
        description: str = '',
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
        label: str = '',
        description: str = '',
        attributes: Optional[dict] = None,
        extras: Optional[dict] = None,
        process_type: Optional[str] = None,
        computer: Optional[orm.Computer] = None,
        store: bool = True,
    ) -> orm.nodes.Node:
        node = orm.CalcJobNode(computer=computer) if process_type else orm.Data(computer=computer)
        node.label = label
        node.description = description
        node.base.attributes.reset(attributes or {})
        node.base.extras.reset(extras or {})
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
        label: str = 'group',
        description: str = '',
        type_string: Optional[str] = None,
    ) -> orm.Group:
        return orm.Group(
            label=label,
            description=description,
            type_string=type_string,
        ).store()

    return _func
