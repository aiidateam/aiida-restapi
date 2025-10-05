"""Test the /computers endpoint"""

from aiida import orm


def test_get_computer_projectable_properties(client):
    """Test get projectable properties for computer."""
    response = client.get('/computers/projectable_properties')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Computer.fields.keys())


def test_get_computers(default_computers, client):  # pylint: disable=unused-argument
    """Test listing existing computer."""
    response = client.get('/computers/')
    assert response.status_code == 200
    assert len(response.json()['results']) == 2


def test_get_computer(default_computers, client):  # pylint: disable=unused-argument
    """Test retrieving a single computer."""
    for comp_id in default_computers:
        response = client.get(f'/computers/{comp_id}')
        assert response.status_code == 200


def test_create_computer(client, authenticate):  # pylint: disable=unused-argument
    """Test creating a new computer."""
    response = client.post(
        '/computers',
        json={
            'label': 'test_comp',
            'hostname': 'fake_host',
            'transport_type': 'core.local',
            'scheduler_type': 'core.pbspro',
        },
    )
    assert response.status_code == 200, response.content
    response = client.get('/computers')
    computers = [comp['label'] for comp in response.json()['results']]
    assert 'test_comp' in computers
