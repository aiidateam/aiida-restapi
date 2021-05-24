# -*- coding: utf-8 -*-
"""Test the /users endpoint"""
from fastapi.testclient import TestClient
from aiida_restapi import app

client = TestClient(app)


def test_get_single_user(default_users):  # pylint: disable=unused-argument
    """Test retrieving a single user."""
    response = client.get('/users/2')
    assert response.status_code == 200
    assert response.json()['first_name'] == 'Giuseppe'


def test_get_users(default_users):  # pylint: disable=unused-argument
    """Test users endpoint.

    Note: Besides the default users set up by the pytest fixture the test profile
    includes a default user.
    """
    response = client.get('/users')
    assert response.status_code == 200
    assert len(response.json()) == 2 + 1
