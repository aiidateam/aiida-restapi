"""Pydantic models for server information and endpoints."""

from __future__ import annotations

import pydantic as pdt


class ServerInfo(pdt.BaseModel):
    """API version information."""

    API_major_version: str = pdt.Field(
        description='Major version of the API',
        examples=['0'],
    )
    API_minor_version: str = pdt.Field(
        description='Minor version of the API',
        examples=['1'],
    )
    API_revision_version: str = pdt.Field(
        description='Revision version of the API',
        examples=['0a1'],
    )
    API_prefix: str = pdt.Field(
        description='Prefix for all API endpoints',
        examples=['/api/v0'],
    )
    AiiDA_version: str = pdt.Field(
        description='Version of the AiiDA installation',
        examples=['2.7.2.post0'],
    )


class ServerEndpoint(pdt.BaseModel):
    """API endpoint."""

    path: str = pdt.Field(
        description='Path of the endpoint',
        examples=['../server/endpoints'],
    )
    group: str | None = pdt.Field(
        description='Group of the endpoint',
        examples=['server'],
    )
    methods: set[str] = pdt.Field(
        description='HTTP methods supported by the endpoint',
        examples=['GET'],
    )
    description: str = pdt.Field(
        '-',
        description='Description of the endpoint',
        examples=['Get a JSON-serializable dictionary of all registered API routes.'],
    )
