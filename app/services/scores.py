from typing import Literal

from app import logger
from app.errors import ServiceError
from app.repositories import scores
from app.repositories.scores import Score


async def create(
    account_id: int,
    online_checksum: str,
    beatmap_md5: str,
    score_points: int,
    performance_points: float,
    accuracy: float,
    highest_combo: int,
    full_combo: bool,
    mods: int,
    num_300s: int,
    num_100s: int,
    num_50s: int,
    num_misses: int,
    num_gekis: int,
    num_katus: int,
    grade: str,  # enum
    submission_status: int,  # enum
    game_mode: int,  # enum
    country: str,
    time_elapsed: int,
    client_anticheat_flags: int,
    client_anticheat_token: str | None,
) -> Score | ServiceError:
    try:
        score = await scores.create(
            account_id,
            online_checksum,
            beatmap_md5,
            score_points,
            performance_points,
            accuracy,
            highest_combo,
            full_combo,
            mods,
            num_300s,
            num_100s,
            num_50s,
            num_misses,
            num_gekis,
            num_katus,
            grade,
            submission_status,
            game_mode,
            country,
            time_elapsed,
            client_anticheat_flags,
            client_anticheat_token,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create score", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return score


async def fetch_many(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
    sort_by: Literal[
        "score",
        "performance_points",
        "accuracy",
        "highest_combo",
        "grade",
    ] = "performance_points",
    page: int | None = None,
    page_size: int | None = None,
) -> list[Score] | ServiceError:
    try:
        _scores = await scores.fetch_many(
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
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch scores", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _scores


async def fetch_count(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
) -> int | ServiceError:
    try:
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
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch scores count", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return total


async def fetch_one(score_id: int) -> Score | ServiceError:
    try:
        score = await scores.fetch_one_by_id(score_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch score", exc_info=exc)
        return ServiceError.SCORES_NOT_FOUND

    if score is None:
        return ServiceError.SCORES_NOT_FOUND

    return score
