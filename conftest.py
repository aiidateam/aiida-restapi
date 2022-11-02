# -*- coding: utf-8 -*-
"""pytest fixtures for simplified testing."""
import tempfile

import pytest
from aiida import orm
from aiida.engine import ProcessState
from aiida.orm import WorkChainNode, WorkFunctionNode
from fastapi.testclient import TestClient

from aiida_restapi import app, config
from aiida_restapi.routers.auth import UserInDB, get_current_user

pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]


@pytest.fixture(scope="function", autouse=True)
def clear_database_auto(clear_database_before_test):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""


@pytest.fixture(scope="function")
def client():
    """Return fastapi test client."""
    yield TestClient(app)


@pytest.fixture(scope="function")
def default_users():
    """Populate database with some users."""
    user_1 = orm.User(
        email="verdi@opera.net", first_name="Giuseppe", last_name="Verdi"
    ).store()
    user_2 = orm.User(
        email="stravinsky@symphony.org", first_name="Igor", last_name="Stravinsky"
    ).store()

    return [user_1.id, user_2.id]


@pytest.fixture(scope="function")
def default_computers():
    """Populate database with some computer"""
    comp_1 = orm.Computer(
        label="test_comp_1",
        hostname="localhost_1",
        transport_type="core.local",
        scheduler_type="core.pbspro",
    ).store()
    comp_2 = orm.Computer(
        label="test_comp_2",
        hostname="localhost_2",
        transport_type="core.local",
        scheduler_type="core.pbspro",
    ).store()

    return [comp_1.id, comp_2.id]


@pytest.fixture(scope="function")
def example_processes():
    """Populate database with some processes"""
    calcs = []
    process_label = "SomeDummyWorkFunctionNode"

    # Create 6 WorkFunctionNodes and WorkChainNodes (one for each ProcessState)
    for state in ProcessState:

        calc = WorkFunctionNode()
        calc.set_process_state(state)

        # Set the WorkFunctionNode as successful
        if state == ProcessState.FINISHED:
            calc.set_exit_status(0)

        # Give a `process_label` to the `WorkFunctionNodes` so the `--process-label` option can be tested
        calc.set_attribute("process_label", process_label)

        calc.store()
        calcs.append(calc.id)

        calc = WorkChainNode()
        calc.set_process_state(state)

        # Set the WorkChainNode as failed
        if state == ProcessState.FINISHED:
            calc.set_exit_status(1)

        # Set the waiting work chain as paused as well
        if state == ProcessState.WAITING:
            calc.pause()

        calc.store()
        calcs.append(calc.id)
    return calcs


@pytest.fixture(scope="function")
def default_test_add_process():
    """Populate database with some node to test adding process"""

    workdir = tempfile.mkdtemp()

    computer = orm.Computer(
        label="localhost",
        hostname="localhost",
        workdir=workdir,
        transport_type="core.local",
        scheduler_type="core.direct",
    )
    computer.store()
    computer.set_minimum_job_poll_interval(0.0)
    computer.configure()

    code = orm.Code(
        input_plugin_name="arithmetic.add", remote_computer_exec=(computer, "/bin/true")
    ).store()

    x = orm.Int(1).store()

    y = orm.Int(2).store()

    return [code.uuid, x.uuid, y.uuid]


@pytest.fixture(scope="function")
def default_groups():
    """Populate database with some groups."""
    test_user_1 = orm.User(
        email="verdi@opera.net", first_name="Giuseppe", last_name="Verdi"
    ).store()
    test_user_2 = orm.User(
        email="stravinsky@symphony.org", first_name="Igor", last_name="Stravinsky"
    ).store()
    group_1 = orm.Group(label="test_label_1", user=test_user_1).store()
    group_2 = orm.Group(label="test_label_2", user=test_user_2).store()
    return [group_1.id, group_2.id]


@pytest.fixture(scope="function")
def default_nodes():
    """Populate database with some nodes."""
    node_1 = orm.Int(1).store()
    node_2 = orm.Float(1.1).store()
    node_3 = orm.Str("test_string").store()
    node_4 = orm.Bool(False).store()

    return [node_1.id, node_2.id, node_3.id, node_4.id]


@pytest.fixture(scope="function")
def authenticate():
    """Authenticate user.

    Since this goes via modifying the app, undo modifications afterwards.
    """

    async def logged_in_user(token=None):  # pylint: disable=unused-argument
        """Fake active user."""
        return UserInDB(**config.fake_users_db["johndoe@example.com"])

    app.dependency_overrides[get_current_user] = logged_in_user
    yield
    app.dependency_overrides = {}
