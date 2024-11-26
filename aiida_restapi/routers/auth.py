"""Handle API authentication and authorization."""

# pylint: disable=missing-function-docstring,missing-class-docstring
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from aiida_restapi.models import User

from ..config import Settings, fake_users_db, get_settings


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str


class UserInDB(User):
    hashed_password: str
    disabled: Optional[bool] = None


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db: dict, email: str) -> Optional[UserInDB]:
    if email in db:
        user_dict = db[email]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db: dict, email: str, password: str) -> Optional[UserInDB]:
    user = get_user(fake_db, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_access_token(settings: Settings, data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.secret_key_algoritm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), settings: Settings = Depends(get_settings)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.secret_key_algoritm])
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception  # pylint: disable=raise-missing-from
    user = get_user(fake_users_db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


@router.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(settings, data={'sub': user.email}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/auth/me/', response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


# @router.get('/users/me/items/')
# async def read_own_items(
#         current_user: User = Depends(get_current_active_user)):
#     return [{'item_id': 'Foo', 'owner': current_user.email}]
