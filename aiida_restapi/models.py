# -*- coding: utf-8 -*-
"""Schemas for AiiDA REST API"""
# pylint: disable=too-few-public-methods

from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """AiiDA User model."""

    id: Optional[int] = Field(description="Unique user id (pk)")
    first_name: Optional[str] = Field(description="First name of the user")
    last_name: Optional[str] = Field(description="Last name of the user")
    institution: Optional[str] = Field(
        description="Host institution or workplace of the user"
    )
    email: str = Field(description="Email address of the user")

    class Config:
        """The models configuration."""

        orm_mode = True
