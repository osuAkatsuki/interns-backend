from uuid import UUID

from fastapi import APIRouter
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.osu_sessions.models import OsuSession
from app.errors import ServiceError
from app.services import osu_sessions


router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case ServiceError.OSU_SESSIONS_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case (ServiceError.INTERNAL_SERVER_ERROR):
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case _:
            logger.warning(
                "Unhandled error code in osu! sessions rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get("/v1/osu_sessions")
async def fetch_many(
    has_any_privilege_bit: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> Success[list[OsuSession]]:
    data = await osu_sessions.fetch_many(
        has_any_privilege_bit=has_any_privilege_bit,
        page=page,
        page_size=page_size,
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch osu! sessions",
            status_code=status_code,
        )

    total = await osu_sessions.fetch_total_count(
        has_any_privilege_bit=has_any_privilege_bit
    )
    if isinstance(total, ServiceError):
        status_code = determine_status_code(total)
        return responses.failure(
            error=total,
            message="Failed to fetch osu! sessions",
            status_code=status_code,
        )

    resp = [OsuSession.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


@router.get("/v1/osu_sessions/{osu_session_id}")
async def fetch_one(osu_session_id: UUID) -> Success[OsuSession]:
    data = await osu_sessions.fetch_by_id(osu_session_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch session",
            status_code=status_code,
        )

    resp = OsuSession.parse_obj(data)
    return responses.success(content=resp)
