from typing import Any

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


async def create(account_id: int, game_mode: int) -> dict[str, Any]:
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
    return dict(stats._mapping)


async def fetch_all(
    account_id: int | None = None,
    game_mode: int | None = None,
) -> list[dict[str, Any]]:
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
    return [dict(stat._mapping) for stat in stats]


async def fetch_many(
    account_id: int | None = None,
    game_mode: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[dict[str, Any]]:
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
    return [dict(stat._mapping) for stat in stats]


async def fetch_one(account_id: int, game_mode: int) -> dict[str, Any] | None:
    stats = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM stats
            WHERE account_id = :account_id
            AND game_mode = :game_mode
        """,
        values={"account_id": account_id, "game_mode": game_mode},
    )
    return dict(stats._mapping) if stats is not None else None
