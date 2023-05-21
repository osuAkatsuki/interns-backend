from typing import Any, TypedDict, cast
from uuid import UUID

from app import clients
from datetime import datetime


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
) -> ClanInvite:
    clan_invite = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO clan_invites (clan_invite_id, clan_id, uses, max_uses, expires_at)
            VALUES (:clan_invite_id, :clan_id, :uses, :max_uses, :expires_at)
            RETURNING {READ_PARAMS}
        """,
        values={
            clan_invite_id: clan_invite_id,
            clan_id: clan_id,
            uses: uses,
            max_uses: max_uses,
            expires_at: expires_at,
        },
    )

    assert clan_invite is not None
    return cast(ClanInvite, clan_invite)


async def fetch_many(
    page: int | None,
    page_size: int | None,
) -> list[ClanInvite] | None:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM clan_invites
    """
    if page is not None and page_size is not None:
        query += """\
            LIMIT :limit
            OFFSET :offset
        """
        values = {
            "page": page,
            "page_size": page_size,
        }

    clan_invites = await clients.database.fetch_all(query, values)

    return [cast(ClanInvite, clan_invite) for clan_invite in clan_invites]


async def fetch_one(clan_invite_id: UUID) -> ClanInvite | None:
    clan_invite = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM clan_invites
            WHERE clan_invite_id = :clan_invite_id
        """,
        values={
            "clan_invite_id": clan_invite_id,
        },
    )

    return cast(ClanInvite, clan_invite) if clan_invite is not None else None