from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients
from app.typing import UNSET
from app.typing import Unset

READ_PARAMS = """\
    clan_id,
    name,
    tag,
    description,
    created_at,
    updated_at
"""


class Clan(TypedDict):
    clan_id: int
    name: str
    tag: str
    description: str
    created_at: datetime
    updated_at: datetime


class ClanUpdateFields(TypedDict, total=False):
    name: str | Unset
    tag: str | Unset
    description: str | Unset


async def create(
    name: str,
    tag: str,
    description: str,
) -> Clan:
    now = datetime.now()

    clan = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO clans (name, tag, description, created_at, updated_at)
                 VALUES (:name, :tag, :description, :created_at, :updated_at)
              RETURNING {READ_PARAMS}
        """,
        values={
            "name": name,
            "tag": tag,
            "description": description,
            "created_at": now,
            "updated_at": now,
        },
    )

    assert clan is not None
    return cast(Clan, clan)


async def fetch_one(clan_id: int) -> Clan | None:
    query = f"""\
        SELECT {READ_PARAMS}
          FROM clans
         WHERE clan_id = :clan_id
    """
    values = {"clan_id": clan_id}
    clan = await clients.database.fetch_one(query, values)
    return cast(Clan, clan) if clan is not None else None


async def fetch_many(
    page: int | None = None,
    page_size: int | None = None,
) -> list[Clan]:
    query = f"""\
        SELECT {READ_PARAMS}
          FROM clans
    """
    values = {}
    if page is not None and page_size is not None:
        query += """\
            LIMIT :limit
           OFFSET :offset
        """
        values["limit"] = page
        values["offset"] = (page - 1) * page_size

    clans = await clients.database.fetch_all(query, values)
    return cast(list[Clan], clans)


async def partial_update(
    clan_id: int,
    name: str | Unset = UNSET,
    tag: str | Unset = UNSET,
    description: str | Unset = UNSET,
) -> Clan | None:
    update_fields: ClanUpdateFields = {}
    if not isinstance(name, Unset):
        update_fields["name"] = name
    if not isinstance(tag, Unset):
        update_fields["tag"] = tag
    if not isinstance(description, Unset):
        update_fields["description"] = description

    query = f"""\
        UPDATE clans
           SET {", ".join(f"{key} = :{key}" for key in update_fields)},
               updated_at = NOW()
         WHERE clan_id = :clan_id
     RETURNING {READ_PARAMS}
    """
    values = {"clan_id": clan_id} | update_fields
    clan = await clients.database.fetch_one(query, values)
    return cast(Clan, clan) if clan is not None else None


async def delete(clan_id: int) -> Clan | None:
    clan = await clients.database.fetch_one(
        query=f"""\
            DELETE FROM clans
                  WHERE clan_id = :clan_id
        """,
        values={
            "clan_id": clan_id,
        },
    )
    return cast(Clan, clan) if clan is not None else None
