from typing import Any

from server import clients

READ_PARAMS = """
    account_id,
    target_id,
    relationship
"""


async def create(
    account_id: int,
    target_id: int,
    relationship: str,
) -> dict[str, Any]:
    channel = await clients.database.fetch_one(
        query=f"""
            INSERT INTO relationships (account_id, target_id, relationship)
            VALUES (:account_id, :target_id, :relationship)
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "target_id": target_id,
            "relationship": relationship,
        },
    )

    assert channel is not None
    return dict(channel._mapping)


async def fetch_all(
    account_id: int | None = None,
    relationship: str | None = None,
) -> list[dict[str, Any]]:
    channels = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM relationships
            WHERE account_id = COALESCE(:account_id, account_id)
            AND relationship = COALESCE(:relationship, relationship)
        """,
        values={"account_id": account_id, "relationship": relationship},
    )

    return [dict(channel._mapping) for channel in channels]


async def remove(
    account_id: int,
    target_id: int,
) -> dict[str, Any] | None:
    channel = await clients.database.fetch_one(
        query=f"""
            DELETE FROM relationships
            WHERE account_id = :account_id
            AND target_id = :target_id
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "target_id": target_id,
        },
    )
    return dict(channel._mapping) if channel is not None else None


async def fetch_one(
    target_id: int,
    account_id: int,
) -> dict[str, Any] | None:
    channel = await clients.database.fetch_one(
        query=f"""
            SELECT {READ_PARAMS}
            FROM relationships
            WHERE account_id = :account_id
            AND target_id = :target_id
        """,
        values={
            "account_id": account_id,
            "target_id": target_id
        },
    )
    return dict(channel._mapping) if channel is not None else None

