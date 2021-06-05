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

    # TODO: Somehow this does not reset the user id counter, which causes the /users/id test to fail  # pylint: disable=fixme


@pytest.fixture(scope="function")
def client():
    """Return fastapi test client."""
    yield TestClient(app)


@pytest.fixture(scope="function")
def default_users():
    """Populate database with some users."""
    orm.User(email="verdi@opera.net", first_name="Giuseppe", last_name="Verdi").store()
    orm.User(
        email="stravinsky@symphony.org", first_name="Igor", last_name="Stravinsky"
    ).store()


@pytest.fixture(scope="function")
def default_computers():
    """Populate database with some computer"""
    orm.Computer(
        label="test_comp_1",
        hostname="localhost_1",
        transport_type="local",
        scheduler_type="pbspro",
    ).store()
    orm.Computer(
        label="test_comp_2",
        hostname="localhost_2",
        transport_type="local",
        scheduler_type="pbspro",
    ).store()


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
