"""Configuration of API"""

from functools import lru_cache

from pydantic_settings import BaseSettings

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Settings(BaseSettings):
    """Configuration settings for the application."""

    # pylint: disable=too-few-public-methods

    class Config:
        """Config settings."""

        env_file = '.env'
        env_file_encoding = 'utf-8'

    secret_key: str = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7'
    """The secret key used to create access tokens."""

    secret_key_algoritm: str = 'HS256'
    """The algorithm used to create access tokens."""

    access_token_expire_minutes: int = 30
    """The number of minutes an access token remains valid."""

    read_only: bool = False
    """Whether the instance is read-only. If set to ``True`` all DELETE, PATCH, POST and PUT methods will raise 405."""


@lru_cache()
def get_settings() -> Settings:
    """Return the configuration settings for the application.

    This function is cached and should be used preferentially over constructing ``Settings`` directly.
    """
    return Settings()


fake_users_db = {
    'johndoe@example.com': {
        'pk': 23,
        'first_name': 'John',
        'last_name': 'Doe',
        'institution': 'EPFL',
        'email': 'johndoe@example.com',
        'hashed_password': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'disabled': False,
    }
}
