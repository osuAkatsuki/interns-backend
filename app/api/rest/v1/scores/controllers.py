from typing import Literal

from fastapi import APIRouter
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.scores.models import Score
from app.errors import ServiceError
from app.services import scores

router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case ServiceError.SCORES_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case ServiceError.INTERNAL_SERVER_ERROR:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case _:
            logger.warning(
                "Unhandled error code in scores rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.get("/v1/scores")
async def fetch_many(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
    sort_by: (
        Literal[
            "score",
            "performance_points",
            "accuracy",
            "highest_combo",
            "grade",
        ]
        | None
    ) = None,
    page: int = 1,
    page_size: int = 50,
) -> Success[list[Score]]:
    data = await scores.fetch_many(
        beatmap_md5=beatmap_md5,
        account_id=account_id,
        country=country,
        full_combo=full_combo,
        grade=grade,
        submission_status=submission_status,
        game_mode=game_mode,
        mods=mods,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch scores",
            status_code=status_code,
        )

    total = await scores.fetch_count(
        beatmap_md5=beatmap_md5,
        account_id=account_id,
        country=country,
        full_combo=full_combo,
        grade=grade,
        submission_status=submission_status,
        game_mode=game_mode,
        mods=mods,
    )
    if isinstance(total, ServiceError):
        status_code = determine_status_code(total)
        return responses.failure(
            error=total,
            message="Failed to fetch scores",
            status_code=status_code,
        )

    resp = [Score.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


@router.get("/v1/scores/{score_id}")
async def fetch_one(score_id: int) -> Success[Score]:
    data = await scores.fetch_one(score_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch score",
            status_code=status_code,
        )

    resp = Score.parse_obj(data)
    return responses.success(content=resp)
