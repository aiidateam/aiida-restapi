# -*- coding: utf-8 -*-
"""Schemas for AiiDA REST API.

Models in this module mirror those in
`aiida/backends/djsite/db/models.py` and `aiida/backends/sqlalchemy/models`
"""
# pylint: disable=too-few-public-methods

from datetime import datetime
from typing import List, Optional, Type, TypeVar, ClassVar

from pydantic import BaseModel, Field

from aiida import orm

ModelType = TypeVar("ModelType", bound="AiidaModel")


class AiidaModel(BaseModel):
    """A mapping of an AiiDA entity to a pydantic model."""

    _orm_entity: ClassVar[Type[orm.entities.Entity]] = orm.entities.Entity

    class Config:
        """The models configuration."""

        orm_mode = True

    @classmethod
    def get_projectable_properties(cls) -> List[str]:
        """Return projectable properties."""
        return list(cls.schema()["properties"].keys())

    @classmethod
    def get_entities(
        cls: Type[ModelType],
        *,
        page_size: Optional[int] = None,
        page: int = 0,
        project: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[ModelType]:
        """Return a list of entities (with pagination).

        :param project: properties to project (default: all available)
        :param page_size: the page size (default: infinite)
        :param page: the page to return, if page_size set
        """
        if project is None:
            project = cls.get_projectable_properties()
        else:
            assert set(cls.get_projectable_properties()).issuperset(
                project
            ), f"projection not subset of projectable properties: {project!r}"
        query = orm.QueryBuilder().append(
            cls._orm_entity, tag="fields", project=project
        )
        if page_size is not None:
            query.offset(page_size * (page - 1))
            query.limit(page_size)
        if order_by is not None:
            assert set(cls.get_projectable_properties()).issuperset(
                order_by
            ), f"order_by not subset of projectable properties: {project!r}"
            query.order_by({"fields": order_by})
        return [cls(**result["fields"]) for result in query.dict()]


class Comment(AiidaModel):
    """AiiDA Comment model."""

    _orm_entity = orm.Comment

    id: Optional[int] = Field(description="Unique comment id (pk)")
    uuid: str = Field(description="Unique comment uuid")
    ctime: Optional[datetime] = Field(description="Creation time")
    mtime: Optional[datetime] = Field(description="Last modification time")
    content: Optional[str] = Field(description="Comment content")
    dbnode_id: Optional[int] = Field(description="Unique node id (pk)")
    user_id: Optional[int] = Field(description="Unique user id (pk)")


class User(AiidaModel):
    """AiiDA User model."""

    _orm_entity = orm.User

    id: Optional[int] = Field(description="Unique user id (pk)")
    email: str = Field(description="Email address of the user")
    first_name: Optional[str] = Field(description="First name of the user")
    last_name: Optional[str] = Field(description="Last name of the user")
    institution: Optional[str] = Field(
        description="Host institution or workplace of the user"
    )
