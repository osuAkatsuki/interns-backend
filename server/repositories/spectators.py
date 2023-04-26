from typing import Any
from uuid import UUID

from server import clients

"""
READ PARAMS
account_id: id of user who's spectating
target_id: id of user who is playing (being spectated)
currently_spectating: True unless stopped in which case delete row
"""

READ_PARAMS = """
    account_id
    target_id
    currently_spectating
"""

async def create(
    account_id: int,
    target_id: int,
    currently_spectating: bool,
) -> dict[str, Any]:
    channel = await clients.database.fetch_one(
        query=f"""
            INSERT INTO spectators (account_id, target_id, currently_spectating)
            VALUES (:account_id, :target_id, :currently_spectating)
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "target_id": target_id,
            "currently_spectating": currently_spectating
        }
    )

    assert channel is not None
    return dict(channel._mapping)


async def fetch_all(
    account_id: int,
    target_id: int,
    currently_spectating: bool,
) -> list[dict[str, Any]]:
    # TODO MAYBE FIX TRUE
    channels = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM spectators
            WHERE account_id = COALESCE(:account_id, account_id)
            AND target_id = COALESCE(:target_id, target_id)
            AND currently_spectating = TRUE
        """,
        values={
            "account_id": account_id,
            "target_id": target_id,
            "currently_spectating": currently_spectating
        },
    )

    return [dict(channel._mapping) for channel in channels]
