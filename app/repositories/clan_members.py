from typing import Any, TypedDict, cast
from datetime import datetime

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


async def fetch_all(
    page: int | None,
    page_size: int | None,
) -> list[ClanMember] | None:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM clan_members
    """
    values = {}
    if page is not None and page_size is not None:
        query += """
            LIMIT :limit
            OFFSET :offset
        """
        values["limit"] = page
        values["offset"] = (page - 1) * page_size

    clan_members = await clients.database.fetch_all(query, values)

    return [cast(ClanMember, clan_member) for clan_member in clan_members]

