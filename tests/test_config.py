"""Tests for machine-local REST API configuration."""

import json

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from aiida_restapi.config import (
    DEFAULT_CORS_ALLOW_ORIGIN_REGEX,
    LOCAL_CONFIG_ENV_VAR,
    load_local_config,
)
from aiida_restapi.main import create_app


def test_load_local_config_defaults(monkeypatch):
    monkeypatch.delenv(LOCAL_CONFIG_ENV_VAR, raising=False)

    config = load_local_config()

    assert config.cors.allow_origins == []
    assert config.cors.allow_origin_regex == DEFAULT_CORS_ALLOW_ORIGIN_REGEX


def test_load_local_config_from_env_path(tmp_path, monkeypatch):
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
    monkeypatch.setenv(LOCAL_CONFIG_ENV_VAR, str(config_path))

    config = load_local_config()

    assert config.cors.allow_origins == ['https://example.org']
    assert config.cors.allow_origin_regex == r'https://.*\.example\.net'


def test_create_app_uses_local_cors_config(tmp_path, monkeypatch):
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
    monkeypatch.setenv(LOCAL_CONFIG_ENV_VAR, str(config_path))

    app = create_app()

    assert any(middleware.cls is CORSMiddleware for middleware in app.user_middleware)

    client = TestClient(app)
    for origin in ('https://example.org', 'https://test.example.net'):
        response = client.get('/v0/server/info', headers={'Origin': origin})
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == origin

    response = client.get('/v0/server/info', headers={'Origin': 'https://other.invalid'})
    assert response.status_code == 200
    assert 'access-control-allow-origin' not in response.headers
