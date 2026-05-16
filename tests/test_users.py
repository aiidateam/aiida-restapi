"""Test the /users endpoint"""

from __future__ import annotations

import pytest
from aiida import orm
from fastapi.testclient import TestClient
from httpx import AsyncClient


def test_get_user_schema(client: TestClient):
    """Test retrieving the user schema."""
    response = client.get('/users/schema')
    assert response.status_code == 200
    result = response.json()
    assert 'properties' in result
    assert sorted(result['properties'].keys()) == sorted(orm.User.fields.keys())


def test_get_user_projections(client: TestClient):
    """Test get projections for users."""
    response = client.get('/users/projections')
    assert response.status_code == 200
    assert response.json() == sorted(orm.User.fields.keys())


@pytest.mark.usefixtures('default_users')
def test_get_users(client: TestClient):
    """Test listing existing users.

    Note: Besides the default users set up by the pytest fixture the test profile
    includes a default user.
    """
    response = client.get('/users')
    assert response.status_code == 200
    assert len(response.json()['data']) == 2 + 1


def test_get_user(client: TestClient, default_users: list[int | None]):
    """Test retrieving a single user."""
    for user_id in default_users:
        response = client.get(f'/users/{user_id}')
        assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.usefixtures('authenticate')
async def test_create_user(async_client: AsyncClient):
    """Test creating a new user."""
    response = await async_client.post('/users', json={'first_name': 'New', 'email': 'aiida@localhost'})
    assert response.status_code == 200, response.content
    attributes = response.json()['data']['attributes']
    assert attributes['first_name'] == 'New'
    assert attributes['email'] == 'aiida@localhost'
