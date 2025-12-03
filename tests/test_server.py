# test the server router

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from aiida_restapi.config import API_CONFIG


def test_get_server_endpoints(client: TestClient):
    response = client.get('/server/endpoints')
    assert response.status_code == 200
    data = response.json()
    assert 'endpoints' in data
    assert isinstance(data['endpoints'], list)
    assert len(data['endpoints']) > 0
    for endpoint in data['endpoints']:
        assert 'path' in endpoint
        assert 'group' in endpoint
        assert 'methods' in endpoint
        assert 'description' in endpoint


def test_get_server_endpoints_table(client: TestClient):
    response = client.get('/server/endpoints/table')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']

    bs = BeautifulSoup(response.text, 'html.parser')
    assert bs.find('table') is not None
    assert len(bs.find_all('th')) == 4

    tbody = bs.find('tbody')
    assert tbody is not None

    for row in tbody.find_all('tr'):
        cols = row.find_all('td')
        path = cols[0].get_text()

        # Check that the group, if not empty, is in path immediately after the prefix
        if (group := cols[1].get_text()) != '-':
            assert path.startswith(f'{client.base_url}{API_CONFIG["PREFIX"]}/{group}')

        # Check that those endpoints that should be links are indeed links
        method = cols[2].get_text()
        if method == 'GET' and 'auth' not in path and '{' not in path:
            assert cols[0].find('a') is not None
        else:
            assert cols[0].find('a') is None
