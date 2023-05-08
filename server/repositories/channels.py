from datetime import datetime
from typing import cast
from typing import TypedDict

from server import clients

READ_PARAMS = """
    channel_id,
    name,
    topic,
    read_privileges,
    write_privileges,
    auto_join,
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
    created_at: datetime
    updated_at: datetime


async def create(
    name: str,
    topic: str,
    read_privileges: str,
    write_privileges: int,
    auto_join: bool,
) -> Channel:
    channel = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO channels (name, topic, read_privileges, write_privileges, auto_join, created_at, updated_at)
            VALUES (:name, :topic, :read_privileges, :write_privileges, :auto_join, :created_at, :updated_at)
            RETURNING {READ_PARAMS}
        """,
        values={
            "name": name,
            "topic": topic,
            "read_privileges": read_privileges,
            "write_privileges": write_privileges,
            "auto_join": auto_join,
        },
    )

    assert channel is not None
    return cast(Channel, channel)


async def fetch_all() -> list[Channel]:
    channels = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM channels
        """
    )

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
