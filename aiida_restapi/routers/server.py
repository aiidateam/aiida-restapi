"""Declaration of FastAPI application."""

from aiida import __version__ as aiida_version
from fastapi import APIRouter
from pydantic import BaseModel

from aiida_restapi.config import API_CONFIG

router = APIRouter()


class ServerInfo(BaseModel):
    """API version information."""

    API_major_version: str
    API_minor_version: str
    API_revision_version: str
    API_prefix: str
    AiiDA_version: str


@router.get('/server/info', response_model=ServerInfo)
async def get_server_info() -> ServerInfo:
    """Get the API version information"""
    api_version = API_CONFIG['VERSION'].split('.')
    return ServerInfo(
        API_major_version=api_version[0],
        API_minor_version=api_version[1],
        API_revision_version=api_version[2],
        API_prefix=API_CONFIG['PREFIX'],
        AiiDA_version=aiida_version,
    )
