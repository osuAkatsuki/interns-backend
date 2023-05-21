from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients


class ClanMember(TypedDict):
    clan_id: int
    account_id: int
    privileges: int
    created_at: datetime
    updated_at: datetime


READ_PARAMS = """\
    clan_id,
    account_id,
    privileges,
    created_at,
    updated_at
"""


async def create(
    clan_id: int,
    account_id: int,
    privileges: int,
) -> ClanMember:
    clan_member = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO clan_members (clan_id, account_id, privileges)
            VALUES (:clan_id, :account_id, :privileges)
            RETURNING {READ_PARAMS}
        """,
        values={
            clan_id: "clan_id",
            account_id: "account_id",
            privileges: "privileges",
        },
    )

    assert clan_member is not None
    return cast(ClanMember, clan_member)


async def fetch_many(
    clan_id: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[ClanMember]:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM clan_members
        WHERE clan_id = COALESCE(:clan_id, clan_id)
    """
    values = {
        "clan_id": clan_id,
    }
    if page is not None and page_size is not None:
        query += """\
            LIMIT :limit
            OFFSET :offset
        """
        values["limit"] = page
        values["offset"] = (page - 1) * page_size

    clan_members = await clients.database.fetch_all(query, values)

    return [cast(ClanMember, clan_member) for clan_member in clan_members]


async def partial_update(
    clan_id: int,
    account_id: int,
    privileges: int | None = None,
) -> ClanMember | None:
    clan_member = await clients.database.fetch_one(
        query=f"""\
            UPDATE clan_members
            SET privileges = COALESSCE(:privileges, privileges)
            WHERE clan_id = :clan_id
            AND account_id = :account_id
        """,
        values={
            "clan_id": clan_id,
            "account_id": account_id,
            "privileges": privileges,
        },
    )

    return cast(ClanMember, clan_member) if clan_member is not None else None


async def delete(clan_id: int, account_id: int) -> ClanMember | None:
    clan_member = await clients.database.fetch_one(
        query=f"""\
            DELETE FROM clan_members
            WHERE clan_id = :clan_id
            AND account_id = :account_id
            RETURNING {READ_PARAMS}
        """,
        values={
            "clan_id": clan_id,
            "account_id": account_id,
        },
    )

    return cast(ClanMember, clan_member) if not None else None


# Written with <3 by MetalFace
