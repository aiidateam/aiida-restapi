# -*- coding: utf-8 -*-
"""Schemas for AiiDA REST API.

Models in this module mirror those in
`aiida.backends.djsite.db.models` and `aiida.backends.sqlalchemy.models`
"""
# pylint: disable=too-few-public-methods

import inspect
import io
from datetime import datetime
from typing import ClassVar, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from aiida import orm
from fastapi import Form
from pydantic import BaseModel, Field

# Template type for subclasses of `AiidaModel`
ModelType = TypeVar("ModelType", bound="AiidaModel")


def as_form(cls: Type[BaseModel]) -> Type[BaseModel]:
    """
    Adds an as_form class method to decorated models. The as_form class method
    can be used with FastAPI endpoints

    Note: Taken from https://github.com/tiangolo/fastapi/issues/2387
    """
    new_params = [
        inspect.Parameter(
            field.alias,
            inspect.Parameter.POSITIONAL_ONLY,
            default=(Form(field.default) if not field.required else Form(...)),
        )
        for field in cls.__fields__.values()
    ]

    async def _as_form(**data: Dict) -> BaseModel:
        return cls(**data)

    sig = inspect.signature(_as_form)
    sig = sig.replace(parameters=new_params)
    _as_form.__signature__ = sig  # type: ignore
    setattr(cls, "as_form", _as_form)
    return cls


class AiidaModel(BaseModel):
    """A mapping of an AiiDA entity to a pydantic model."""

    _orm_entity: ClassVar[Type[orm.entities.Entity]] = orm.entities.Entity

    class Config:
        """The models configuration."""

        orm_mode = True
        extra = "forbid"

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

    class Config:
        """The models configuration."""

        extra = "allow"

    id: Optional[int] = Field(description="Unique user id (pk)")
    email: str = Field(description="Email address of the user")
    first_name: Optional[str] = Field(description="First name of the user")
    last_name: Optional[str] = Field(description="Last name of the user")
    institution: Optional[str] = Field(
        description="Host institution or workplace of the user"
    )


class Computer(AiidaModel):
    """AiiDA Computer Model."""

    _orm_entity = orm.Computer

    id: Optional[int] = Field(description="Unique computer id (pk)")
    uuid: Optional[str] = Field(description="Unique id for computer")
    label: str = Field(description="Used to identify a computer. Must be unique")
    hostname: Optional[str] = Field(
        description="Label that identifies the computer within the network"
    )
    scheduler_type: Optional[str] = Field(
        description="The scheduler (and plugin) that the computer uses to manage jobs"
    )
    transport_type: Optional[str] = Field(
        description="The transport (and plugin) \
                    required to copy files and communicate to and from the computer"
    )
    metadata: Optional[dict] = Field(
        description="General settings for these communication and management protocols"
    )

    description: Optional[str] = Field(description="Description of node")


class Node(AiidaModel):
    """AiiDA Node Model."""

    _orm_entity = orm.Node

    id: Optional[int] = Field(description="Unique id (pk)")
    uuid: Optional[UUID] = Field(description="Unique uuid")
    node_type: Optional[str] = Field(description="Node type")
    process_type: Optional[str] = Field(description="Process type")
    label: str = Field(description="Label of node")
    description: Optional[str] = Field(description="Description of node")
    ctime: Optional[datetime] = Field(description="Creation time")
    mtime: Optional[datetime] = Field(description="Last modification time")
    user_id: Optional[int] = Field(description="Created by user id (pk)")
    dbcomputer_id: Optional[int] = Field(description="Associated computer id (pk)")
    attributes: Optional[Dict] = Field(
        description="Variable attributes of the node",
    )
    extras: Optional[Dict] = Field(
        description="Variable extras (unsealed) of the node",
    )
    repository_metadata: Optional[Dict] = Field(
        description="Metadata about file repository associated with this node",
    )


@as_form
class Node_Post(AiidaModel):
    """AiiDA model for posting Nodes."""

    entry_point: str = Field(description="Entry_point")
    process_type: Optional[str] = Field(description="Process type")
    label: Optional[str] = Field(description="Label of node")
    description: Optional[str] = Field(description="Description of node")
    user_id: Optional[int] = Field(description="Created by user id (pk)")
    dbcomputer_id: Optional[int] = Field(description="Associated computer id (pk)")
    attributes: Optional[Dict] = Field(
        description="Variable attributes of the node",
    )
    extras: Optional[Dict] = Field(
        description="Variable extras (unsealed) of the node",
    )

    @classmethod
    def create_new_node(
        cls: Type[ModelType],
        orm_class: orm.Node,
        node_dict: dict,
    ) -> orm.Node:
        """Create and Store new Node"""
        attributes = node_dict.pop("attributes", {})
        extras = node_dict.pop("extras", {})
        repository_metadata = node_dict.pop("repository_metadata", {})

        if issubclass(orm_class, orm.BaseType):
            orm_object = orm_class(
                attributes["value"],
                **node_dict,
            )
        elif issubclass(orm_class, orm.Dict):
            orm_object = orm_class(
                dict=attributes,
                **node_dict,
            )
        elif issubclass(orm_class, orm.InstalledCode):
            orm_object = orm_class(
                computer=orm.load_computer(pk=node_dict.get("dbcomputer_id")),
                filepath_executable=attributes["filepath_executable"],
            )
            orm_object.label = node_dict.get("label")
        elif issubclass(orm_class, orm.PortableCode):
            orm_object = orm_class(
                computer=orm.load_computer(pk=node_dict.get("dbcomputer_id")),
                filepath_executable=attributes["filepath_executable"],
                filepath_files=attributes["filepath_files"],
            )
            orm_object.label = node_dict.get("label")
        else:
            orm_object = orm_class(**node_dict)
            orm_object.base.attributes.set_many(attributes)

        orm_object.base.extras.set_many(extras)
        orm_object.base.repository.repository_metadata = repository_metadata
        orm_object.store()
        return orm_object

    @classmethod
    def create_new_node_with_file(
        cls: Type[ModelType],
        orm_class: orm.Node,
        node_dict: dict,
        file: bytes,
    ) -> orm.Node:
        """Create and Store new Node with file"""
        attributes = node_dict.pop("attributes", {})
        extras = node_dict.pop("extras", {})

        orm_object = orm_class(file=io.BytesIO(file), **node_dict, **attributes)

        orm_object.base.extras.set_many(extras)
        orm_object.store()
        return orm_object


class Group(AiidaModel):
    """AiiDA Group model."""

    _orm_entity = orm.Group

    id: int = Field(description="Unique id (pk)")
    uuid: UUID = Field(description="Universally unique id")
    label: str = Field(description="Label of group")
    type_string: str = Field(description="type of the group")
    description: Optional[str] = Field(description="Description of group")
    extras: Optional[Dict] = Field(description="extra data about for the group")
    time: datetime = Field(description="Created time")
    user_id: int = Field(description="Created by user id (pk)")

    @classmethod
    def from_orm(cls, orm_entity: orm.Group) -> orm.Group:
        query = (
            orm.QueryBuilder()
            .append(
                cls._orm_entity,
                filters={"id": orm_entity.id},
                tag="fields",
                project=["user_id", "time"],
            )
            .limit(1)
        )
        orm_entity.user_id = query.dict()[0]["fields"]["user_id"]
        orm_entity.time = query.dict()[0]["fields"]["time"]

        return super().from_orm(orm_entity)


class Group_Post(AiidaModel):
    """AiiDA Group Post model."""

    _orm_entity = orm.Group

    label: str = Field(description="Used to access the group. Must be unique.")
    type_string: Optional[str] = Field(description="Type of the group")
    description: Optional[str] = Field(description="Short description of the group.")


class Process(AiidaModel):
    """AiiDA Process Model"""

    _orm_entity = orm.ProcessNode

    id: Optional[int] = Field(description="Unique id (pk)")
    uuid: Optional[UUID] = Field(description="Universally unique identifier")
    node_type: Optional[str] = Field(description="Node type")
    process_type: Optional[str] = Field(description="Process type")
    label: str = Field(description="Label of node")
    description: Optional[str] = Field(description="Description of node")
    ctime: Optional[datetime] = Field(description="Creation time")
    mtime: Optional[datetime] = Field(description="Last modification time")
    user_id: Optional[int] = Field(description="Created by user id (pk)")
    dbcomputer_id: Optional[int] = Field(description="Associated computer id (pk)")
    attributes: Optional[Dict] = Field(
        description="Variable attributes of the node",
    )
    extras: Optional[Dict] = Field(
        description="Variable extras (unsealed) of the node",
    )
    repository_metadata: Optional[Dict] = Field(
        description="Metadata about file repository associated with this node",
    )


class Process_Post(AiidaModel):
    """AiiDA Process Post Model"""

    label: str = Field(description="Label of node")
    inputs: dict = Field(description="Input parmeters")
    process_entry_point: str = Field(description="Entry Point for process")
