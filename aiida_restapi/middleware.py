"""Module with middleware."""

from typing import Callable

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .config import Settings, get_settings


async def protected_methods_middleware(request: Request, call_next: Callable[[Request], Response]) -> Response:
    """Middleware that will return a 405 if the instance is read only and the request method is mutating.

    Mutating request methods are `DELETE`, `PATCH`, `POST`, `PUT`.
    """
    settings: Settings = get_settings()

    if settings.read_only and request.method in {'DELETE', 'PATCH', 'POST', 'PUT'}:
        return JSONResponse(
            status_code=405,
            content=jsonable_encoder({'reason': 'This instance is read-only.'}),
            media_type='application/json',
        )

    return await call_next(request)
