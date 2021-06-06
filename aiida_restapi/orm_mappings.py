# -*- coding: utf-8 -*-
"""The 'source of truth' for database entity fields."""
from datetime import datetime
from typing import Dict, Optional, Type
from uuid import UUID

from aiida import orm
from pydantic import BaseModel, Field, Json


class AuthInfo(BaseModel):
    """AiiDA AuthInfo SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    aiidauser_id: int = Field(description="Relates to user")
    dbcomputer_id: int = Field(description="Relates to computer")
    metadata: Json = Field(description="Metadata of the authorisation")
    auth_params: Json = Field(description="Parameters of the authorisation")
    enabled: bool = Field(description="Whether the computer is enabled", default=True)


class Comment(BaseModel):
    """AiiDA Comment SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    uuid: UUID = Field(description="Unique uuid")
    ctime: datetime = Field(description="Creation time")
    mtime: datetime = Field(description="Last modification time")
    content: Optional[str] = Field(description="Content of the comment")
    user_id: int = Field(description="Created by user id (pk)")
    dbnode_id: int = Field(description="Associated node id (pk)")


class Computer(BaseModel):
    """AiiDA Computer SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    uuid: UUID = Field(description="Unique uuid")
    name: str = Field(description="Computer name")
    hostname: str = Field(description="Computer name")
    description: Optional[str] = Field(description="Computer name")
    scheduler_type: str = Field(description="Scheduler type")
    transport_type: str = Field(description="Transport type")
    metadata: Json = Field(description="Metadata of the computer")


class Group(BaseModel):
    """AiiDA Group SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    uuid: UUID = Field(description="Unique uuid")
    label: str = Field(description="Label of group")
    type_string: str = Field(description="type of the group")
    time: datetime = Field(description="Created time")
    description: Optional[str] = Field(description="Description of group")
    extras: Json = Field(description="extra data about for the group")
    user_id: int = Field(description="Created by user id (pk)")


class Log(BaseModel):
    """AiiDA Log SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    uuid: UUID = Field(description="Unique uuid")
    time: datetime = Field(description="Creation time")
    loggername: str = Field(description="The loggers name")
    levelname: str = Field(description="The log level")
    message: Optional[str] = Field(description="The log message")
    metadata: Json = Field(description="Metadata associated with the log")
    dbnode_id: int = Field(description="Associated node id (pk)")


class Node(BaseModel):
    """AiiDA Node SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    uuid: UUID = Field(description="Unique uuid")
    node_type: str = Field(description="Node type")
    process_type: str = Field(description="Process type")
    label: Optional[str] = Field(description="Label of node")
    description: Optional[str] = Field(description="Description of node")
    ctime: datetime = Field(description="Creation time")
    mtime: datetime = Field(description="Last modification time")
    user_id: int = Field(description="Created by user id (pk)")
    dbcomputer_id: Optional[int] = Field(description="Associated computer id (pk)")
    attributes: Json = Field(
        description="Variable attributes of the node",
    )
    extras: Json = Field(
        description="Variable extras (unsealed) of the node",
    )


class User(BaseModel):
    """AiiDA User SQL table fields."""

    id: int = Field(description="Unique id (pk)")
    email: str = Field(description="Email address of the user")
    first_name: Optional[str] = Field(description="First name of the user")
    last_name: Optional[str] = Field(description="Last name of the user")
    institution: Optional[str] = Field(
        description="Host institution or workplace of the user"
    )


ORM_MAPPING: Dict[Type[orm.Entity], Type[BaseModel]] = {
    orm.AuthInfo: AuthInfo,
    orm.Comment: Comment,
    orm.Computer: Computer,
    orm.Group: Group,
    orm.Log: Log,
    orm.nodes.Node: Node,
    orm.User: User,
}
