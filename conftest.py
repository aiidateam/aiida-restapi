# -*- coding: utf-8 -*-
"""pytest fixtures for simplified testing."""
import pytest
from aiida import orm
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


@pytest.fixture(scope='function', autouse=True)
def clear_database_auto(clear_database_before_test):  # pylint: disable=unused-argument
    """Automatically clear database in between tests."""

    # todo: For some reason this does not seem to take effect  # pylint: disable=fixme
    # (database is not cleared between tests)


@pytest.fixture(scope='function')
def default_users():
    """Populate database with some users.
    """
    orm.User(email='verdi@opera.net', first_name='Giuseppe',
             last_name='Verdi').store()
    orm.User(email='stravinsky@symphony.org',
             first_name='Igor',
             last_name='Stravinsky').store()
