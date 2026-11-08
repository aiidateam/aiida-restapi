"""Configuration of API"""

import os
from pathlib import Path

import pydantic as pdt

from aiida_restapi import __version__

API_CONFIG = {
    'PREFIX': '/v0',
    'VERSION': __version__,
}

DEFAULT_CORS_ALLOW_ORIGIN_REGEX = r'https?://(localhost|127\.0\.0\.1)(:\d+)?'
LOCAL_CONFIG_ENV_VAR = 'AIIDA_RESTAPI_CONFIG'


class CorsConfig(pdt.BaseModel):
    """Local CORS settings."""

    model_config = pdt.ConfigDict(extra='forbid')

    allow_origins: list[str] = pdt.Field(
        default_factory=list,
        description='List of allowed CORS origins',
    )
    allow_origin_regex: str = pdt.Field(
        DEFAULT_CORS_ALLOW_ORIGIN_REGEX,
        description='Regex for allowed CORS origins',
    )


class LocalApiConfig(pdt.BaseModel):
    """Machine-local settings for a REST API instance."""

    model_config = pdt.ConfigDict(extra='forbid')

    cors: CorsConfig = pdt.Field(
        default_factory=CorsConfig,
        description='CORS configuration for the API',
    )


def load_local_config(path: str | Path | None = None) -> LocalApiConfig:
    """Load machine-local API configuration from JSON, if configured."""
    config_path = path or os.getenv(LOCAL_CONFIG_ENV_VAR)
    if config_path is None:
        return LocalApiConfig()

    path = Path(config_path).expanduser()
    return LocalApiConfig.model_validate_json(path.read_text(encoding='utf8'))
