from app import clients


async def get_global_rank(account_id: int, game_mode: int) -> int:
    """Get the global rank of an account for a given game mode."""
    global_rank = await clients.database.fetch_val(
        query="""\
            SELECT ROW_NUMBER() OVER (ORDER BY performance_points DESC) AS rank
            FROM stats
            WHERE account_id = :account_id
            AND game_mode = :game_mode
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
        },
    )
    assert global_rank is not None
    return global_rank


async def get_country_rank(
    account_id: int,
    game_mode: int,
    country: str,
) -> int:
    """Get the country rank of an account for a given game mode."""
    global_rank = await clients.database.fetch_val(
        query="""\
            SELECT ROW_NUMBER() OVER (ORDER BY performance_points DESC) AS rank
            FROM stats
            WHERE account_id = :account_id
            AND game_mode = :game_mode
            AND country = :country
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
            "country": country,
        },
    )
    return global_rank
