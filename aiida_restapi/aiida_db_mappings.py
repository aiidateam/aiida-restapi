"""The 'source of truth' for mapping AiiDA's database table models to pydantic models.

Note in the future we may want to do this programmatically, however, there are two issues:
- AiiDA uses both SQLAlchemy and Django backends, so one would need to be chosen
- Neither model includes descriptions of fields
"""

from datetime import datetime
from typing import Dict, Optional, Type
from uuid import UUID

from aiida import orm
from pydantic import BaseModel, Field, Json


class AuthInfo(BaseModel):
    """AiiDA AuthInfo SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    aiidauser_id: int = Field(description='Relates to user')
    dbcomputer_id: int = Field(description='Relates to computer')
    metadata: Json = Field(description='Metadata of the authorisation')
    auth_params: Json = Field(description='Parameters of the authorisation')
    enabled: bool = Field(description='Whether the computer is enabled', default=True)


class Comment(BaseModel):
    """AiiDA Comment SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    uuid: UUID = Field(description='Universally unique id')
    ctime: datetime = Field(description='Creation time')
    mtime: datetime = Field(description='Last modification time')
    content: Optional[str] = Field(None, description='Content of the comment')
    user_id: int = Field(description='Created by user id (pk)')
    dbnode_id: int = Field(description='Associated node id (pk)')


class Computer(BaseModel):
    """AiiDA Computer SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    uuid: UUID = Field(description='Universally unique id')
    label: str = Field(description='Computer name')
    hostname: str = Field(description='Identifier for the computer within the network')
    description: Optional[str] = Field(None, description='Description of the computer')
    scheduler_type: str = Field(description='Scheduler plugin type, to manage compute jobs')
    transport_type: str = Field(description='Transport plugin type, to manage file transfers')
    metadata: Json = Field(description='Metadata of the computer')


class Group(BaseModel):
    """AiiDA Group SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    uuid: UUID = Field(description='Universally unique id')
    label: str = Field(description='Label of group')
    type_string: str = Field(description='type of the group')
    time: datetime = Field(description='Created time')
    description: Optional[str] = Field(None, description='Description of group')
    extras: Json = Field(description='extra data about for the group')
    user_id: int = Field(description='Created by user id (pk)')


class Log(BaseModel):
    """AiiDA Log SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    uuid: UUID = Field(description='Universally unique id')
    time: datetime = Field(description='Creation time')
    loggername: str = Field(description='The loggers name')
    levelname: str = Field(description='The log level')
    message: Optional[str] = Field(None, description='The log message')
    metadata: Json = Field(description='Metadata associated with the log')
    dbnode_id: int = Field(description='Associated node id (pk)')


class Node(BaseModel):
    """AiiDA Node SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    uuid: UUID = Field(description='Universally unique id')
    node_type: str = Field(description='Node type')
    process_type: str = Field(description='Process type')
    label: str = Field(description='Label of node')
    description: str = Field(description='Description of node')
    ctime: datetime = Field(description='Creation time')
    mtime: datetime = Field(description='Last modification time')
    user_id: int = Field(description='Created by user id (pk)')
    dbcomputer_id: Optional[int] = Field(None, description='Associated computer id (pk)')
    attributes: Json = Field(
        description='Attributes of the node (immutable after storing the node)',
    )
    extras: Json = Field(
        description='Extra attributes of the node (mutable)',
    )


class User(BaseModel):
    """AiiDA User SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    email: str = Field(description='Email address of the user')
    first_name: Optional[str] = Field(None, description='First name of the user')
    last_name: Optional[str] = Field(None, description='Last name of the user')
    institution: Optional[str] = Field(None, description='Host institution or workplace of the user')


class Link(BaseModel):
    """AiiDA Link SQL table fields."""

    id: int = Field(description='Unique id (pk)')
    input_id: int = Field(description='Unique id (pk) of the input node')
    output_id: int = Field(description='Unique id (pk) of the output node')
    label: Optional[str] = Field(None, description='The label of the link')
    type: str = Field(description='The type of link')


ORM_MAPPING: Dict[str, Type[BaseModel]] = {
    'AuthInfo': AuthInfo,
    'Comment': Comment,
    'Computer': Computer,
    'Group': Group,
    'Log': Log,
    'Node': Node,
    'User': User,
    'Link': Link,
}


def get_model_from_orm(orm_cls: Type[orm.Entity], allow_subclasses: bool = True) -> Type[BaseModel]:
    """Return the pydantic model related to the orm class.

    :param allow_subclasses: Return the base class mapping for subclasses
    """
    if orm_cls.__name__ in ORM_MAPPING:
        return ORM_MAPPING[orm_cls.__name__]
    if allow_subclasses and issubclass(orm_cls, orm.nodes.Node):
        return Node
    if allow_subclasses and issubclass(orm_cls, orm.Group):
        return Group
    raise KeyError(f'{orm_cls}')
