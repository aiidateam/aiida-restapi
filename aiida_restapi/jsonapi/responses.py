"""JSON:API responses module."""

from __future__ import annotations

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .models.base import JsonApiBaseDocument


class JsonApiResponse(JSONResponse):
    """Custom JSONResponse for JSON:API media type."""

    media_type = 'application/vnd.api+json'

    def render(self, content: JsonApiBaseDocument) -> bytes:
        content = jsonable_encoder(content, exclude_none=True)
        return super().render(content)
