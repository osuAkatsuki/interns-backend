from datetime import datetime
from typing import Any, TypedDict, cast
from server import clients

READ_PARAMS = "clan_id, name, tag, description, created_at, updated_at"


class Clan(TypedDict):
    name: str
    tag: str
    description: str
    created_at: datetime
    updated_at: datetime


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
    clan = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM clans
            WHERE clan_id = :clan_id
        """,
        values={
            "clan_id": clan_id,
        },
    )

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


async def update_by_id(
    clan_id: int,
    name: str | None = None,
    tag: str | None = None,
    description: str | None = None,
) -> Clan | None:
    updated_at = datetime.now()

    clan = await clients.database.fetch_one(
        query=f"""\
            UPDATE clans
            SET name = COALESCE(:name, name),
            tag = COALESCE(:tag, tag),
            description(:description, description)
            WHERE clan_id = :clan_id
            RETURNING {READ_PARAMS}
        """,
        values={
            "clan_id": clan_id,
            "name": name,
            "tag": tag,
            "description": description,
            "updated_at": updated_at,
        },
    )
    return cast(Clan, clan) if clan is not None else None


async def delete_by_id(clan_id) -> Clan | None:
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
