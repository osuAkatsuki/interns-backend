from app import clients


async def get_global_rank(account_id: int, game_mode: int) -> int:
    """Get the global rank of an account for a given game mode."""
    global_rank = await clients.database.fetch_val(
        query="""\
            WITH global_rankings AS (
                SELECT account_id, game_mode, ROW_NUMBER() OVER (
                    PARTITION BY game_mode
                    ORDER BY performance_points DESC
                ) AS rank
                FROM stats
            )
            SELECT rank
            FROM global_rankings
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
            WITH country_rankings AS (
                SELECT stats.account_id, stats.game_mode, accounts.country, ROW_NUMBER() OVER (
                    PARTITION BY (stats.game_mode, accounts.country)
                    ORDER BY stats.performance_points DESC
                ) AS rank
                FROM stats
                LEFT JOIN accounts ON accounts.account_id = stats.account_id
            )
            SELECT rank
            FROM country_rankings
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
