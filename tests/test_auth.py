# -*- coding: utf-8 -*-
"""Test the /users endpoint"""
from fastapi.testclient import TestClient
from aiida_restapi import app

client = TestClient(app)


def test_authenticate_user():
    """Test authenticating as a user.
    """
    # authenticate with username and password
    response = client.post('/token',
                           data={
                               'username': 'johndoe@example.com',
                               'password': 'secret'
                           })
    assert response.status_code == 200, response.content
    token = response.json()['access_token']

    # use JSON web token to access protected endpoint
    response = client.get('/auth/me',
                          headers={'Authorization': 'Bearer ' + str(token)})
    assert response.status_code == 200, response.content
    assert response.json()['last_name'] == 'Doe'
