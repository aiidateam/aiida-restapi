"""Pydantic models for profile discovery."""

from __future__ import annotations

import pydantic as pdt


class ProfileList(pdt.BaseModel):
    """Profiles available through the REST API."""

    profiles: list[str] = pdt.Field(description='Profiles available through the REST API.')
    default_profile: str | None = pdt.Field(description='The name of the configured default profile.')
