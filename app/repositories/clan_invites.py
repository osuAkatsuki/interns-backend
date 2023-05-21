from datetime import datetime
from typing import Any
from typing import cast
from typing import TypedDict
from uuid import UUID

from app import clients


class ClanInvite(TypedDict):
    clan_invite_id: UUID
    clan_id: int
    uses: int
    max_uses: int | None
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
    max_uses: int | None,
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
    page: int | None = None,
    page_size: int | None = None,
) -> list[ClanInvite] | None:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM clan_invites
    """
    values = {}
    if page is not None and page_size is not None:
        query += """\
            LIMIT :limit
            OFFSET :offset
        """
        values["offset"] = page
        values["limit"] = (page - 1) * page_size

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


async def partial_update(
    clan_invite_id: UUID,
    clan_id: int | None = None,
    uses: int | None = None,
    expires_at: datetime | None = None,
) -> ClanInvite | None:
    clan_invite = await clients.database.fetch_one(
        query=f"""\
            UPDATE clan_invites
            SET clan_id = COALESCE(:clan_id, clan_id),
            uses = COALESCE(:uses, uses),
            expires_at = COALESCE(:expires_at, expires_at)
            WHERE clan_invite_id = :clan_invite_id
            RETURNING {READ_PARAMS}
        """,
        values={
            "clan_invite_id": clan_invite_id,
            "clan_id": clan_id,
            "uses": uses,
            "expires_at": expires_at,
        },
    )

    return cast(ClanInvite, clan_invite) if not None else None
