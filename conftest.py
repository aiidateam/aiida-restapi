# -*- coding: utf-8 -*-
"""pytest fixtures for simplified testing."""
import pytest
from aiida import orm
from fastapi.testclient import TestClient

from aiida_restapi import app, config
from aiida_restapi.routers.auth import UserInDB, get_current_user

pytest_plugins = ["aiida.manage.tests.pytest_fixtures"]


@pytest.fixture(scope="function", autouse=True)
def clear_database_auto(clear_database_before_test):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""

    # TODO: Somehow this does not reset the user id counter, which causes the /users/id test to fail


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
        transport_type="local",
        scheduler_type="pbspro",
    ).store()
    comp_2 = orm.Computer(
        label="test_comp_2",
        hostname="localhost_2",
        transport_type="local",
        scheduler_type="pbspro",
    ).store()

    return [comp_1.id, comp_2.id]


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
