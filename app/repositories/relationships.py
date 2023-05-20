from typing import cast
from typing import Literal
from typing import TypedDict

from app import clients

READ_PARAMS = """
    account_id,
    target_id,
    relationship
"""


class Relationship(TypedDict):
    account_id: int
    target_id: int
    # TODO: rename to type or relationship_type?
    relationship: Literal["friend", "blocked"]


async def create(
    account_id: int,
    target_id: int,
    relationship: str,
) -> Relationship:
    _relationship = await clients.database.fetch_one(
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

    assert _relationship is not None
    return cast(Relationship, _relationship)


async def fetch_all(
    account_id: int | None = None,
    relationship: str | None = None,
) -> list[Relationship]:
    relationships = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM relationships
            WHERE account_id = COALESCE(:account_id, account_id)
            AND relationship = COALESCE(:relationship, relationship)
        """,
        values={"account_id": account_id, "relationship": relationship},
    )
    return cast(list[Relationship], relationships)


async def remove(
    account_id: int,
    target_id: int,
) -> Relationship | None:
    relationship = await clients.database.fetch_one(
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
    return cast(Relationship, relationship)


async def fetch_one(
    target_id: int,
    account_id: int,
) -> Relationship | None:
    relationship = await clients.database.fetch_one(
        query=f"""
            SELECT {READ_PARAMS}
            FROM relationships
            WHERE account_id = :account_id
            AND target_id = :target_id
        """,
        values={"account_id": account_id, "target_id": target_id},
    )
    return cast(Relationship, relationship)
