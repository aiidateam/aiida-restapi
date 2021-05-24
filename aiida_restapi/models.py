# -*- coding: utf-8 -*-
"""Schemas for AiiDA REST API"""
# pylint: disable=too-few-public-methods

# from datetime import datetime
# from typing import List, Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """AiiDA User model."""
    id: int
    first_name = Field(default='AiiDA', description='First Name of the user')
    last_name = Field(default='User', description='Last Name of the user')
    institution = Field(
        default='EPFL',
        description='Host institution or workplace of the user')
    email = Field(default='aiida@localhost',
                  description='Email Address of the user')

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


# external_data = {
#     'id': '123',
#     'signup_ts': '2019-06-01 12:22',
#     'friends': [1, 2, '3'],
# }
# user = User(**external_data)
# print(user.id)
# #> 123
# print(repr(user.signup_ts))
# #> datetime.datetime(2019, 6, 1, 12, 22)
# print(user.friends)
# #> [1, 2, 3]
# print(user.dict())
# """
# {
#     'id': 123,
#     'signup_ts': datetime.datetime(2019, 6, 1, 12, 22),
#     'friends': [1, 2, 3],
#     'name': 'John Doe',
# }
