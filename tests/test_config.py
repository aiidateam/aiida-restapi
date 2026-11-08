"""Tests for machine-local REST API configuration."""

import json

import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from aiida_restapi.config import (
    API_CONFIG_ENV_VAR,
    DEFAULT_CORS_ALLOW_ORIGIN_REGEX,
    load_config,
)
from aiida_restapi.main import create_app


def test_load_config_defaults(monkeypatch):
    monkeypatch.delenv(API_CONFIG_ENV_VAR, raising=False)

    config = load_config()

    assert config.cors.allow_origins == []
    assert config.cors.allow_origin_regex == DEFAULT_CORS_ALLOW_ORIGIN_REGEX


def test_load_config_from_env_path(tmp_path, monkeypatch):
    config_path = tmp_path / 'restapi.json'
    config_path.write_text(
        json.dumps(
            {
                'cors': {
                    'allow_origins': ['https://example.org'],
                    'allow_origin_regex': r'https://.*\.example\.net',
                }
            }
        ),
        encoding='utf8',
    )
    monkeypatch.setenv(API_CONFIG_ENV_VAR, str(config_path))

    config = load_config()

    assert config.cors.allow_origins == ['https://example.org']
    assert config.cors.allow_origin_regex == r'https://.*\.example\.net'


@pytest.mark.parametrize(
    ('allow_origin_regex', 'allowed_origins', 'denied_origins'),
    [
        (
            DEFAULT_CORS_ALLOW_ORIGIN_REGEX,
            ['http://localhost', 'https://localhost:8000', 'http://127.0.0.1:5173'],
            ['http://localhost.example.org', 'http://127.0.0.2:5173', 'https://localhost:not-a-port'],
        ),
        (
            r'https://.*\.example\.net(:\d+)?',
            ['https://ui.example.net', 'https://nested.ui.example.net:9443'],
            ['http://ui.example.net', 'https://example.net', 'https://ui.example.org'],
        ),
        (
            r'https?://localhost:(3000|5173)',
            ['http://localhost:3000', 'https://localhost:5173'],
            ['http://localhost', 'http://localhost:8000', 'https://localhost:3000.example.org'],
        ),
    ],
)
def test_create_app_applies_cors_origin_regex(
    tmp_path,
    monkeypatch,
    allow_origin_regex,
    allowed_origins,
    denied_origins,
):
    config_path = tmp_path / 'restapi.json'
    config_path.write_text(
        json.dumps(
            {
                'cors': {
                    'allow_origins': [],
                    'allow_origin_regex': allow_origin_regex,
                }
            }
        ),
        encoding='utf8',
    )
    monkeypatch.setenv(API_CONFIG_ENV_VAR, str(config_path))

    app = create_app()

    assert any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)

    client = TestClient(app)
    for origin in allowed_origins:
        response = client.get('/v0/server/info', headers={'Origin': origin})
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == origin

    for origin in denied_origins:
        response = client.get('/v0/server/info', headers={'Origin': origin})
        assert response.status_code == 200
        assert 'access-control-allow-origin' not in response.headers
