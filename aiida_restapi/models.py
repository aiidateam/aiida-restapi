# -*- coding: utf-8 -*-
"""Schemas for AiiDA REST API"""
# pylint: disable=too-few-public-methods

import typing
from pydantic import BaseModel, Field


class User(BaseModel):
    """AiiDA User model."""
    id: typing.Optional[int] = Field(description='Unique user id (pk)')
    first_name: typing.Optional[str] = Field(
        description='First name of the user')
    last_name: typing.Optional[str] = Field(
        description='Last name of the user')
    institution: typing.Optional[str] = Field(
        description='Host institution or workplace of the user')
    email: str = Field(description='Email address of the user')

    @staticmethod
    def from_orm(ormobj):
        """Create AiiDA User instance from AiiDA orm."""
        return User(
            id=ormobj.id,
            first_name=ormobj.first_name,
            last_name=ormobj.last_name,
            email=ormobj.email,
            institution=ormobj.institution,
        )
