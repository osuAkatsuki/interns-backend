from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients

READ_PARAMS = """
    channel_id,
    name,
    topic,
    read_privileges,
    write_privileges,
    auto_join,
    temporary,
    created_at,
    updated_at
"""


class Channel(TypedDict):
    channel_id: int
    name: str
    topic: str
    read_privileges: int
    write_privileges: int
    auto_join: bool
    temporary: bool
    created_at: datetime
    updated_at: datetime


async def create(
    name: str,
    topic: str,
    read_privileges: int,
    write_privileges: int,
    auto_join: bool,
    temporary: bool,
) -> Channel:
    channel = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO channels (name, topic, read_privileges, write_privileges, auto_join, temporary)
            VALUES (:name, :topic, :read_privileges, :write_privileges, :auto_join, :temporary)
            RETURNING {READ_PARAMS}
        """,
        values={
            "name": name,
            "topic": topic,
            "read_privileges": read_privileges,
            "write_privileges": write_privileges,
            "auto_join": auto_join,
            "temporary": temporary,
        },
    )

    assert channel is not None
    return cast(Channel, channel)


async def fetch_many(
    read_privileges: int | None = None,
    write_privileges: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[Channel]:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM channels
        WHERE write_privileges = COALESCE(:write_privileges, write_privileges)
        AND read_privileges = COALESCE(:read_privileges, read_privileges)
    """
    values = {
        "write_privileges": write_privileges,
        "read_privileges": read_privileges,
    }
    if page is not None and page_size is not None:
        query += """\
            LIMIT :page_size
            OFFSET :offset
        """
        values["page_size"] = page_size
        values["offset"] = (page - 1) * page_size
    channels = await clients.database.fetch_all(query, values)
    return cast(list[Channel], channels)


async def fetch_one(channel_id: int) -> Channel | None:
    channel = await clients.database.fetch_one(
        query=f"""
            SELECT {READ_PARAMS}
            from channels
            WHERE channel_id = :channel_id
        """,
        values={
            "channel_id": channel_id,
        },
    )

    return cast(Channel, channel) if channel is not None else None


async def fetch_one_by_name(name: str) -> Channel | None:
    channel = await clients.database.fetch_one(
        query=f"""
            SELECT {READ_PARAMS}
            from channels
            WHERE name = :name
        """,
        values={
            "name": name,
        },
    )

    return cast(Channel, channel) if channel is not None else None


async def delete(channel_id: int) -> None:
    await clients.database.execute(
        query=f"""
            DELETE FROM channels
            WHERE channel_id = :channel_id
        """,
        values={
            "channel_id": channel_id,
        },
    )
