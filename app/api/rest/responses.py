from typing import Any
from typing import Generic
from typing import Literal
from typing import TypeVar

from fastapi import Response
from fastapi import status
from pydantic import BaseModel
from pydantic.generics import GenericModel

from app import json
from app.errors import ServiceError

T = TypeVar("T")


class Success(GenericModel, Generic[T]):
    status: Literal["success"]
    data: T
    meta: dict[str, Any]  # TODO: non-total typeddict?


def success(
    content: Any,
    status_code: int = status.HTTP_200_OK,
    headers: dict[str, str] | None = None,
    meta: dict[str, Any] | None = None,
) -> Any:
    if meta is None:
        meta = {}
    data = {"status": "success", "data": content, "meta": meta}
    return json.ORJSONResponse(data, status_code, headers)


def no_content(headers: dict[str, str] | None = None) -> Any:
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)


class Failure(BaseModel):
    status: Literal["error"]
    error: ServiceError
    message: str


def failure(
    error: ServiceError,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    headers: dict[str, str] | None = None,
) -> Any:
    data = {"status": "error", "error": error, "message": message}
    return json.ORJSONResponse(data, status_code, headers)
