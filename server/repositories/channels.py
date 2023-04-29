from typing import Any

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


async def create(
    name: str,
    topic: str,
    read_privileges: str,
    write_privileges: int,
    auto_join: bool,
) -> dict[str, Any]:
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
    return channel


async def fetch_all() -> list[dict[str, Any]]:
    channels = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
            FROM channels
        """
    )

    return [channel for channel in channels]


async def fetch_one(channel_id: int) -> dict[str, Any] | None:
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

    return channel if channel is not None else None


async def fetch_one_by_name(name: str) -> dict[str, Any] | None:
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

    return channel if channel is not None else None
