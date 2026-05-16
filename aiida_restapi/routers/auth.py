"""Handle API authentication and authorization."""

from __future__ import annotations

import json
import os
import typing as t
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import bcrypt
from aiida import orm
from aiida.common.exceptions import NotExistent
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

from aiida_restapi import config


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str


class UserInDB(orm.User.ReadModel):
    hashed_password: str
    disabled: t.Optional[bool] = None


class CredentialRecord(BaseModel):
    hashed_password: str
    disabled: bool = False


pwd_context = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f'{config.API_CONFIG["PREFIX"]}/auth/token')

read_router = APIRouter(prefix='/auth')
write_router = APIRouter(prefix='/auth')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith('$argon2'):
        try:
            return pwd_context.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    if hashed_password.startswith('$2b$'):
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _parse_credentials(payload: t.Any) -> dict[str, CredentialRecord]:
    if not isinstance(payload, dict):
        raise ValueError('Credential payload must be a JSON object keyed by user email.')

    credentials: dict[str, CredentialRecord] = {}
    for email, raw_credential in payload.items():
        if isinstance(raw_credential, str):
            credentials[email] = CredentialRecord(hashed_password=raw_credential)
        elif isinstance(raw_credential, dict):
            credentials[email] = CredentialRecord(**raw_credential)
        else:
            raise ValueError(f'Credential entry for `{email}` must be a hash string or object.')

    return credentials


@lru_cache(maxsize=1)
def load_credentials() -> dict[str, CredentialRecord]:
    credentials_json = os.getenv('AIIDA_RESTAPI_AUTH_CREDENTIALS_JSON')
    credentials_file = os.getenv('AIIDA_RESTAPI_AUTH_CREDENTIALS_FILE')

    if credentials_json and credentials_file:
        raise RuntimeError(
            'Set only one of AIIDA_RESTAPI_AUTH_CREDENTIALS_JSON or AIIDA_RESTAPI_AUTH_CREDENTIALS_FILE.'
        )

    if credentials_json:
        try:
            payload = json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError('Invalid JSON in AIIDA_RESTAPI_AUTH_CREDENTIALS_JSON.') from exc
        return _parse_credentials(payload)

    if credentials_file:
        try:
            payload = json.loads(Path(credentials_file).read_text(encoding='utf-8'))
        except OSError as exc:
            raise RuntimeError(f'Unable to read credentials file: {credentials_file}') from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f'Invalid JSON in credentials file: {credentials_file}') from exc
        return _parse_credentials(payload)

    return {}


def clear_credentials_cache() -> None:
    load_credentials.cache_clear()


def get_user(email: str) -> UserInDB | None:
    try:
        aiida_user = orm.User.collection.get(email=email)
    except NotExistent:
        return None

    credential = load_credentials().get(email)
    if credential is None:
        return None

    return UserInDB(
        pk=aiida_user.pk,
        email=aiida_user.email,
        first_name=aiida_user.first_name,
        last_name=aiida_user.last_name,
        institution=aiida_user.institution,
        hashed_password=credential.hashed_password,
        disabled=credential.disabled,
    )


def authenticate_user(email: str, password: str) -> UserInDB | None:
    user = get_user(email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: t.Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email = payload.get('sub')
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception  # pylint: disable=raise-missing-from
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: t.Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


@write_router.post(
    '/token',
    response_model=Token,
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, t.Any]:
    """Login to get access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.email}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@read_router.get(
    '/me/',
    response_model=orm.User.ReadModel,
)
async def read_users_me(
    current_user: t.Annotated[orm.User.ReadModel, Depends(get_current_active_user)],
) -> orm.User.ReadModel:
    """Get the current authenticated user."""
    return current_user
