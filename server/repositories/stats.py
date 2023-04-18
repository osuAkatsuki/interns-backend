from typing import cast
from typing import TypedDict

from server import clients

READ_PARAMS = """
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
    return cast(Stats, dict(stats._mapping))


async def fetch_all(
    account_id: int | None = None,
    game_mode: int | None = None,
) -> list[Stats]:
    stats = await clients.database.fetch_all(
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
    return [cast(Stats, dict(stat._mapping)) for stat in stats]


async def fetch_many(
    account_id: int | None = None,
    game_mode: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[Stats]:
    stats = await clients.database.fetch_all(
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
    return [cast(Stats, dict(stat._mapping)) for stat in stats]


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
    return cast(Stats, dict(stats._mapping)) if stats is not None else None
