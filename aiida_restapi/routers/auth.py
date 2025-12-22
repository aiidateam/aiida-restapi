"""Handle API authentication and authorization."""

from __future__ import annotations

import typing as t
from datetime import datetime, timedelta, timezone

import bcrypt
from aiida import orm
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


class UserInDB(orm.User.Model):
    hashed_password: str
    disabled: t.Optional[bool] = None


pwd_context = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f'{config.API_CONFIG["PREFIX"]}/auth/token')

router = APIRouter(prefix='/auth')


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


def get_user(db: dict, email: str) -> UserInDB | None:
    if email in db:
        user_dict = db[email]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db: dict, email: str, password: str) -> UserInDB | None:
    user = get_user(fake_db, email)

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


async def get_current_user(token: t.Annotated[str, Depends(oauth2_scheme)]) -> orm.User.Model:
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
    user = get_user(config.fake_users_db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: t.Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


@router.post(
    '/token',
    response_model=Token,
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, t.Any]:
    """Login to get access token."""
    user = authenticate_user(config.fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.email}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get(
    '/me/',
    response_model=orm.User.Model,
)
async def read_users_me(
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.User.Model:
    """Get the current authenticated user."""
    return current_user
