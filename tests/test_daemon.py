"""Test the /daemon endpoint"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.usefixtures('stopped_daemon_client', 'authenticate')
def test_status_and_start(client: TestClient):
    """Test ``/daemon/status`` when the daemon is not running and ``/daemon/start``."""
    response = client.get('/daemon/status')
    assert response.status_code == 200, response.content

    results = response.json()
    assert results['running'] is False
    assert results['num_workers'] is None

    response = client.post('/daemon/start')
    assert response.status_code == 200, response.content

    results = response.json()
    assert results['running'] is True
    assert results['num_workers'] == 1

    response = client.post('/daemon/start')
    assert response.status_code == 400, response.content


@pytest.mark.usefixtures('started_daemon_client', 'authenticate')
def test_status_and_stop(client: TestClient):
    """Test ``/daemon/status`` when the daemon is running and ``/daemon/stop``."""
    response = client.get('/daemon/status')
    assert response.status_code == 200, response.content

    results = response.json()
    assert results['running'] is True
    assert results['num_workers'] == 1

    response = client.post('/daemon/stop')
    assert response.status_code == 200, response.content

    results = response.json()
    assert results['running'] is False
    assert results['num_workers'] is None

    response = client.post('/daemon/stop')
    assert response.status_code == 400, response.content
