"""Test the /groups endpoint"""

from aiida import orm


def test_get_group_projectable_properties(client):
    """Test get projectable properties for group."""
    response = client.get('/groups/projectable_properties')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Group.fields.keys())


def test_get_groups(default_groups, client):  # pylint: disable=unused-argument
    """Test listing existing groups."""
    response = client.get('/groups')
    assert response.status_code == 200
    assert len(response.json()['results']) == 2


def test_get_group(default_groups, client):  # pylint: disable=unused-argument
    """Test retrieving a single group."""
    for group_id in default_groups:
        response = client.get(f'/groups/{group_id}')
        assert response.status_code == 200


def test_create_group(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new group."""
    response = client.post('/groups', json={'label': 'test_label_create'})
    assert response.status_code == 200, response.content
    assert response.json()['user']
    response = client.get('/groups')
    first_names = [group['label'] for group in response.json()['results']]
    assert 'test_label_create' in first_names
