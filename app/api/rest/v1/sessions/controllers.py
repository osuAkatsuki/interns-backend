from uuid import UUID

from fastapi import APIRouter
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.sessions.models import Session
from app.errors import ServiceError
from app.services import sessions

router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case ServiceError.CREDENTIALS_NOT_FOUND:
            return status.HTTP_401_UNAUTHORIZED
        case ServiceError.CREDENTIALS_INCORRECT:
            return status.HTTP_401_UNAUTHORIZED
        case ServiceError.INTERNAL_SERVER_ERROR:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case ServiceError.SESSIONS_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case _:
            logger.warning(
                "Unhandled error code in sessions rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


# TODO: fetch_many, down the stack
@router.get("/v1/sessions")
async def fetch_all() -> Success[list[Session]]:
    data = await sessions.fetch_all()
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch sessions",
            status_code=status_code,
        )

    resp = [Session.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={},
    )


@router.get("/v1/sessions/{session_id}")
async def fetch_one(session_id: UUID) -> Success[Session]:
    data = await sessions.fetch_one(session_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch session",
            status_code=status_code,
        )

    resp = Session.parse_obj(data)
    return responses.success(content=resp)


# TODO: PATCH /v1/sessions/{session_id}


@router.delete("/v1/sessions/{session_id}")
async def delete(session_id: UUID) -> Success[Session]:
    data = await sessions.delete(session_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to delete session",
            status_code=status_code,
        )

    resp = Session.parse_obj(data)
    return responses.success(content=resp)
