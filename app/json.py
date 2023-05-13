import uuid
from typing import Any

import orjson
from asyncpg.pgproto import pgproto
from fastapi.responses import JSONResponse
from pydantic import BaseModel


def _default_processor(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return _default_processor(data.dict())
    elif isinstance(data, dict):
        return {k: _default_processor(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_default_processor(v) for v in data]
    elif isinstance(data, (uuid.UUID, pgproto.UUID)):
        return str(data)
    else:
        return data


def dumps(data: Any) -> bytes:
    return orjson.dumps(data, default=_default_processor)


def loads(data: str) -> Any:
    return orjson.loads(data)


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return dumps(content)
