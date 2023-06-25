from fastapi import APIRouter
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.stats.models import Stats
from app.errors import ServiceError
from app.services import stats

router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case ServiceError.INTERNAL_SERVER_ERROR:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case ServiceError.ACCOUNTS_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case _:
            logger.warning(
                "Unhandled error code in stats rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get("/v1/stats")
async def fetch_many(
    account_id: int | None = None,
    game_mode: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> Success[list[Stats]]:
    data = await stats.fetch_many(
        account_id=account_id,
        game_mode=game_mode,
        page=page,
        page_size=page_size,
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch stats",
            status_code=status_code,
        )

    total = await stats.fetch_total_count(
        account_id=account_id,
        game_mode=game_mode,
    )
    if isinstance(total, ServiceError):
        status_code = determine_status_code(total)
        return responses.failure(
            error=total,
            message="Failed to fetch stats",
            status_code=status_code,
        )

    resp = [Stats.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


@router.get("/v1/stats/{account_id}/{game_mode}")
async def fetch_one(account_id: int, game_mode: int) -> Success[Stats]:
    data = await stats.fetch_one(account_id, game_mode)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch stats",
            status_code=status_code,
        )

    resp = Stats.parse_obj(data)
    return responses.success(content=resp)
