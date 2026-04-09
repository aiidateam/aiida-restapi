"""Configuration of API"""

from aiida_restapi import __version__

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

API_CONFIG = {
    'PREFIX': '/v0',
    'VERSION': __version__,
}
