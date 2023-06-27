from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients
from app.typing import UNSET
from app.typing import Unset


class ClanMember(TypedDict):
    clan_id: int
    account_id: int
    privileges: int
    created_at: datetime
    updated_at: datetime


class ClanUpdateFields(TypedDict, total=False):
    privileges: int | Unset


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
    privileges: int | Unset = UNSET,
) -> ClanMember | None:
    update_fields: ClanUpdateFields = {}
    if not isinstance(privileges, Unset):
        update_fields["privileges"] = privileges

    query = f"""\
        UPDATE clan_members
           SET {", ".join(f"{key} = :{key}" for key in update_fields)},
               updated_at = NOW()
         WHERE clan_id = :clan_id
           AND account_id = :account_id
     RETURNING {READ_PARAMS}
    """
    values = {"clan_id": clan_id, "account_id": account_id} | update_fields
    clan_member = await clients.database.fetch_one(query, values)
    return cast(ClanMember, clan_member) if clan_member is not None else None


async def delete(clan_id: int, account_id: int) -> ClanMember | None:
    query = f"""\
        DELETE FROM clan_members
              WHERE clan_id = :clan_id
                AND account_id = :account_id
          RETURNING {READ_PARAMS}
    """
    values = {"clan_id": clan_id, "account_id": account_id}
    clan_member = await clients.database.fetch_one(query, values)
    return cast(ClanMember, clan_member) if not None else None


# Written with <3 by MetalFace
