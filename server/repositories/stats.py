from typing import cast
from typing import TypedDict

from server import clients

READ_PARAMS = """\
    account_id,
    game_mode,
    total_score,
    ranked_score,
    performance_points,
    play_count,
    play_time,
    accuracy,
    highest_combo,
    total_hits,
    replay_views,
    xh_count,
    x_count,
    sh_count,
    s_count,
    a_count
"""


class Stats(TypedDict):
    account_id: int
    game_mode: int
    total_score: int
    ranked_score: int
    performance_points: int
    play_count: int
    play_time: int
    accuracy: float
    highest_combo: int
    total_hits: int
    replay_views: int
    xh_count: int
    x_count: int
    sh_count: int
    s_count: int
    a_count: int


def serialize(stats: Stats) -> dict:
    return {
        "account_id": stats["account_id"],
        "game_mode": stats["game_mode"],
        "total_score": stats["total_score"],
        "ranked_score": stats["ranked_score"],
        "performance_points": stats["performance_points"],
        "play_count": stats["play_count"],
        "play_time": stats["play_time"],
        "accuracy": stats["accuracy"],  # should not need to be decimal
        "highest_combo": stats["highest_combo"],
        "total_hits": stats["total_hits"],
        "replay_views": stats["replay_views"],
        "xh_count": stats["xh_count"],
        "x_count": stats["x_count"],
        "sh_count": stats["sh_count"],
        "s_count": stats["s_count"],
        "a_count": stats["a_count"],
    }


def deserialize(stats: dict) -> Stats:
    return {
        "account_id": stats["account_id"],
        "game_mode": stats["game_mode"],
        "total_score": stats["total_score"],
        "ranked_score": stats["ranked_score"],
        "performance_points": stats["performance_points"],
        "play_count": stats["play_count"],
        "play_time": stats["play_time"],
        "accuracy": float(stats["accuracy"]),
        "highest_combo": stats["highest_combo"],
        "total_hits": stats["total_hits"],
        "replay_views": stats["replay_views"],
        "xh_count": stats["xh_count"],
        "x_count": stats["x_count"],
        "sh_count": stats["sh_count"],
        "s_count": stats["s_count"],
        "a_count": stats["a_count"],
    }


async def create(account_id: int, game_mode: int) -> Stats:
    stats = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO stats (account_id, game_mode)
            VALUES (:account_id, :game_mode)
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
        },
    )

    assert stats is not None
    return deserialize(stats)


# TODO: combine these


async def fetch_all(
    account_id: int | None = None,
    game_mode: int | None = None,
) -> list[Stats]:
    all_stats = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM stats
            WHERE account_id = COALESCE(:account_id, account_id)
            AND game_mode = COALESCE(:game_mode, game_mode)
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
        },
    )
    return [deserialize(stats) for stats in all_stats]


async def fetch_many(
    account_id: int | None = None,
    game_mode: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[Stats]:
    all_stats = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM stats
            WHERE account_id = COALESCE(:account_id, account_id)
            AND game_mode = COALESCE(:game_mode, game_mode)
            LIMIT :limit
            OFFSET :offset
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )
    return [deserialize(stats) for stats in all_stats]


async def fetch_one(account_id: int, game_mode: int) -> Stats | None:
    stats = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM stats
            WHERE account_id = :account_id
            AND game_mode = :game_mode
        """,
        values={"account_id": account_id, "game_mode": game_mode},
    )
    return deserialize(stats) if stats is not None else None


async def partial_update(
    account_id: int,
    game_mode: int,
    total_score: int | None = None,
    ranked_score: int | None = None,
    performance_points: int | None = None,
    play_count: int | None = None,
    play_time: int | None = None,
    accuracy: float | None = None,
    highest_combo: int | None = None,
    total_hits: int | None = None,
    replay_views: int | None = None,
    xh_count: int | None = None,
    x_count: int | None = None,
    sh_count: int | None = None,
    s_count: int | None = None,
    a_count: int | None = None,
) -> Stats | None:
    stats = await clients.database.fetch_one(
        query=f"""\
            UPDATE stats
            SET total_score = COALESCE(:total_score, total_score),
                ranked_score = COALESCE(:ranked_score, ranked_score),
                performance_points = COALESCE(:performance_points, performance_points),
                play_count = COALESCE(:play_count, play_count),
                play_time = COALESCE(:play_time, play_time),
                accuracy = COALESCE(:accuracy, accuracy),
                highest_combo = COALESCE(:highest_combo, highest_combo),
                total_hits = COALESCE(:total_hits, total_hits),
                replay_views = COALESCE(:replay_views, replay_views),
                xh_count = COALESCE(:xh_count, xh_count),
                x_count = COALESCE(:x_count, x_count),
                sh_count = COALESCE(:sh_count, sh_count),
                s_count = COALESCE(:s_count, s_count),
                a_count = COALESCE(:a_count, a_count)
            WHERE account_id = :account_id
            AND game_mode = :game_mode
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
            "total_score": total_score,
            "ranked_score": ranked_score,
            "performance_points": performance_points,
            "play_count": play_count,
            "play_time": play_time,
            "accuracy": accuracy,
            "highest_combo": highest_combo,
            "total_hits": total_hits,
            "replay_views": replay_views,
            "xh_count": xh_count,
            "x_count": x_count,
            "sh_count": sh_count,
            "s_count": s_count,
            "a_count": a_count,
        },
    )
    return deserialize(stats) if stats is not None else None
