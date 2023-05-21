from typing import Any, TypedDict, cast
from uuid import UUID

from app import clients
from datetime import datetime

# C R U


class ClanInvite(TypedDict):
    clan_invite_id: UUID
    clan_id: int
    uses: int
    max_uses: int
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


READ_PARAMS = """\
    clan_invite_id,
    clan_id,
    uses,
    max_uses,
    expires_at,
    created_at,
    updated_at
"""


async def create(
    clan_invite_id: UUID,
    clan_id: int,
    uses: int,
    max_uses: int,
    expires_at: datetime,
) -> dict[str, Any]:
    now = datetime.now()
    created_at = now
    updated_at = now

    clan_invite = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO clan_invites (clan_invite_id, clan_id, uses, max_uses, expires_at, created_at, updated_at)
            VALUES (:clan_invite_id, :clan_id, :uses, :max_uses, :expires_at, :created_at, :updated_at)
            RETURNING {READ_PARAMS}
        """,
        values={
            clan_invite_id: clan_invite_id,
            clan_id: clan_id,
            uses: uses,
            max_uses: max_uses,
            expires_at: expires_at,
            created_at: created_at,
            updated_at: updated_at,
        },
    )

    assert clan_invite is not None
    return cast(ClanInvite, clan_invite)


