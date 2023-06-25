from fastapi import APIRouter
from fastapi import status

from uuid import UUID

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.sessions.models import Session
from app.errors import ServiceError
from app.services import sessions


router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case (
            ServiceError.INTERNAL_SERVER_ERROR
            | ServiceError.SESSIONS_FETCH_BY_ID_FAILED
            | ServiceError.SESSIONS_FETCH_MANY_FAILED
            | ServiceError.SESSIONS_FETCH_TOTAL_COUNT_FAILED
            | ServiceError.SESSIONS_FETCH_ALL_FAILED
            | ServiceError.SESSIONS_CREATE_FAILED
            | ServiceError.SESSIONS_UPDATE_FAILED
            | ServiceError.SESSIONS_DELETE_FAILED
        ):
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case ServiceError.SESSIONS_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case _:
            logger.warning(
                "Unhandled error code in sessions rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get("/v1/sessions")
async def fetch_many(
    has_any_privilege_bit: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> Success[list[Session]]:
    data = await sessions.fetch_many(
        has_any_privilege_bit=has_any_privilege_bit,
        page=page,
        page_size=page_size,
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch sessions",
            status_code=status_code,
        )

    total = await sessions.fetch_total_count(
        has_any_privilege_bit=has_any_privilege_bit
    )
    if isinstance(total, ServiceError):
        status_code = determine_status_code(total)
        return responses.failure(
            error=total,
            message="Failed to fetch sessions",
            status_code=status_code,
        )

    resp = [Session.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


@router.get("/v1/sessions/{account_id}")
async def fetch_one(session_id: UUID) -> Success[Session]:
    data = await sessions.fetch_by_id(session_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch session",
            status_code=status_code,
        )

    resp = Session.parse_obj(data)
    return responses.success(content=resp)
