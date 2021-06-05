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


class Computer(BaseModel):
    """AiiDA Computer Model."""

    id: Optional[int] = Field(description="Unique computer id (pk)")
    uuid: Optional[str] = Field(description="Unique id for computer")
    label: str = Field(description="Used to identify a computer. Must be unique")
    hostname: Optional[str] = Field(
        description="Label that identifies the computer within the network"
    )
    scheduler_type: Optional[str] = Field(
        description="Information of the scheduler (and plugin) that the computer uses to manage jobs"
    )
    transport_type: Optional[str] = Field(
        description="Information of the transport (and plugin) \
                    required to copy files and communicate to and from the computer"
    )
    metadata: Optional[dict] = Field(
        description="General settings for these communication and management protocols"
    )

    class Config:
        """The models configuration."""

        orm_mode = True
