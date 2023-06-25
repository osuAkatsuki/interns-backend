from app import logger
from app.errors import ServiceError
from app.repositories import stats
from app.repositories.stats import Stats
from app.typing import UNSET
from app.typing import Unset


async def create(account_id: int, game_mode: int) -> Stats | ServiceError:
    try:
        user_stats = await stats.create(
            account_id=account_id,
            game_mode=game_mode,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create stats", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return user_stats


async def fetch_many(
    account_id: int | None = None,
    game_mode: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[Stats] | ServiceError:
    try:
        _stats = await stats.fetch_many(
            account_id=account_id,
            game_mode=game_mode,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch stats", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _stats


async def fetch_total_count(
    account_id: int | None = None,
    game_mode: int | None = None,
) -> int | ServiceError:
    try:
        total = await stats.fetch_total_count(
            account_id=account_id,
            game_mode=game_mode,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch stats total count", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return total


async def fetch_one(
    account_id: int,
    game_mode: int,
) -> Stats | ServiceError:
    try:
        user_stats = await stats.fetch_one(
            account_id=account_id,
            game_mode=game_mode,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch stats", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if user_stats is None:
        return ServiceError.ACCOUNTS_NOT_FOUND

    return user_stats


async def partial_update(
    account_id: int,
    game_mode: int,
    total_score: int | Unset = UNSET,
    ranked_score: int | Unset = UNSET,
    performance_points: int | Unset = UNSET,
    play_count: int | Unset = UNSET,
    play_time: int | Unset = UNSET,
    accuracy: float | Unset = UNSET,
    highest_combo: int | Unset = UNSET,
    total_hits: int | Unset = UNSET,
    replay_views: int | Unset = UNSET,
    xh_count: int | Unset = UNSET,
    x_count: int | Unset = UNSET,
    sh_count: int | Unset = UNSET,
    s_count: int | Unset = UNSET,
    a_count: int | Unset = UNSET,
) -> Stats | ServiceError:
    try:
        user_stats = await stats.partial_update(
            account_id=account_id,
            game_mode=game_mode,
            total_score=total_score,
            ranked_score=ranked_score,
            performance_points=performance_points,
            play_count=play_count,
            play_time=play_time,
            accuracy=accuracy,
            highest_combo=highest_combo,
            total_hits=total_hits,
            replay_views=replay_views,
            xh_count=xh_count,
            x_count=x_count,
            sh_count=sh_count,
            s_count=s_count,
            a_count=a_count,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to update stats", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if user_stats is None:
        return ServiceError.ACCOUNTS_NOT_FOUND

    return user_stats
