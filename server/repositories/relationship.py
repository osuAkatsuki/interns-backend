from typing import Any

from server import clients

READ_PARAMS = """
    initiator_account_id,
    recipient_account_id,
    relationship,
"""


async def create(
    initiator_account_id: int,
    recipient_account_id: int,
    relationship: str,
) -> dict[str, Any]:
    channel = await clients.database.fetch_one(
        query=f"""
            INSERT INTO relationship (initiator_account_id, recipient_account_id, relationship)
            VALUES (:initiator_account_id, :recipient_account_id, :relationship)
            RETURNING {READ_PARAMS}
        """,
        values={
            "initiator_account_id": initiator_account_id,
            "recipient_account_id": recipient_account_id,
            "relationship": relationship,
        },
    )

    assert channel is not None

    return dict(channel._mapping)


async def fetch_all(
        initiator_account_id: int,
        relationship: str,
) -> dict[str, Any]:
    channels = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM relationship
            WHERE initiator_account_id = COALESCE(:initiator_account_id)
            AND relationship = COALESCE(:relationship)
        """,
        values={
            "initiator_account_id": initiator_account_id,
            "relationship": relationship,
        }
    )

    return [dict(channel._mapping) for channel in channels]


async def remove(
    initiator_account_id: int,
    recipient_account_id: int,
    relationship: str,
) -> dict[str, Any]:
    channel = await clients.database.fetch_all(
        query=f"""
            UPDATE {READ_PARAMS}
            FROM relationship
            SET relationship = NULL
            WHERE initiator_account_id = :initiator_account_id
            AND recipient_account_id = :recipient_account_id
            AND relationship = :relationship
        """,
        values={
            "initiator_account_id": initiator_account_id,
            "recipient_account_id": recipient_account_id,
            "relationship": relationship,
        },
    )
    return dict(channel._mapping)


async def block(
    initiator_account_id: int,
    recipient_account_id: int,
    relationship: str,
):
    ...


async def unblock(
    initiator_account_id: int,
    recipient_account_id: int,
    relationship: str,
): 
    ...
