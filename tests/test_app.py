# test main application

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_read_only_mode(read_only_app: FastAPI):
    client = TestClient(read_only_app)
    response = client.get('/computers/')
    assert response.status_code == 200
    response = client.post('/computers/', json={'name': 'new_computer'})
    assert response.status_code == 405
