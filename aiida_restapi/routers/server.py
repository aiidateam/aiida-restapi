"""Declaration of FastAPI application."""

from typing import Any

from aiida import __version__ as aiida_version
from fastapi import APIRouter

from aiida_restapi.config import API_CONFIG

router = APIRouter()


@router.get('/server/info', response_model=dict[str, Any])
async def get_server_info() -> dict[str, Any]:
    """Get the API version information"""
    response = {}
    api_version = API_CONFIG['VERSION'].split('.')
    response['API_major_version'] = api_version[0]
    response['API_minor_version'] = api_version[1]
    response['API_revision_version'] = api_version[2]
    # Add Rest API prefix
    response['API_prefix'] = API_CONFIG['PREFIX']

    # Add AiiDA version
    response['AiiDA_version'] = aiida_version
    return response
