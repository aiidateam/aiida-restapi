"""Test the /users endpoint"""

import json

from fastapi.testclient import TestClient

from aiida_restapi.routers.auth import clear_credentials_cache, get_password_hash


def test_authenticate_user(client: TestClient, create_user, monkeypatch):
    """Test authenticating as a user."""
    create_user(
        email='johndoe@example.com',
        first_name='John',
        last_name='Doe',
        institution='EPFL',
    )
    monkeypatch.setenv(
        'AIIDA_RESTAPI_AUTH_CREDENTIALS_JSON',
        json.dumps({'johndoe@example.com': {'hashed_password': get_password_hash('secret')}}),
    )
    clear_credentials_cache()

    # authenticate with username and password
    response = client.post('/auth/token', data={'username': 'johndoe@example.com', 'password': 'secret'})
    assert response.status_code == 200, response.content
    token = response.json()['access_token']

    # use JSON web token to access protected endpoint
    response = client.get('/auth/me', headers={'Authorization': 'Bearer ' + str(token)})
    assert response.status_code == 200, response.content
    assert response.json()['last_name'] == 'Doe'

    monkeypatch.delenv('AIIDA_RESTAPI_AUTH_CREDENTIALS_JSON')
    clear_credentials_cache()
