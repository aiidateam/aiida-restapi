"""Configuration of API"""

from aiida_restapi import __version__

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
PASSWORD_HASH = '$argon2id$v=19$m=65536,t=3,p=4$BuglBHdyBnY1lFMo02RVsw$mG+0KHRBW+Cnf5ic+1FrGbfIjCGMLdULtiRoznfuFIA'

fake_users_db = {
    'johndoe@example.com': {
        'pk': 23,
        'first_name': 'John',
        'last_name': 'Doe',
        'institution': 'EPFL',
        'email': 'johndoe@example.com',
        'hashed_password': PASSWORD_HASH,
        'disabled': False,
    }
}

API_CONFIG = {
    'PREFIX': '/api/v0',
    'VERSION': __version__,
}
