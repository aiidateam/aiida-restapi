"""Test the /users endpoint"""

import pytest
from aiida import orm


def test_get_user_projectable_properties(client):
    """Test get projectable properties for users."""
    response = client.get('/users/projectable_properties')
    assert response.status_code == 200
    assert response.json() == sorted(orm.User.fields.keys())


def test_get_users(default_users, client):  # pylint: disable=unused-argument
    """Test listing existing users.

    Note: Besides the default users set up by the pytest fixture the test profile
    includes a default user.
    """
    response = client.get('/users')
    assert response.status_code == 200
    assert len(response.json()['results']) == 2 + 1


def test_get_user(default_users, client):  # pylint: disable=unused-argument
    """Test retrieving a single user."""
    for user_id in default_users:
        response = client.get(f'/users/{user_id}')
        assert response.status_code == 200


@pytest.mark.anyio
async def test_create_user(async_client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new user."""
    response = await async_client.post('/users', json={'first_name': 'New', 'email': 'aiida@localhost'})
    assert response.status_code == 200, response.content
    response = await async_client.get('/users')
    first_names = [user['first_name'] for user in response.json()['results']]
    assert 'New' in first_names
