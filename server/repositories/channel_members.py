from typing import Literal
from uuid import UUID

from server import clients


def make_key(channel_id: int | Literal["*"]) -> str:
    return f"server:channel-members:{channel_id}"


def serialize(session_id: UUID) -> str:
    return str(session_id)


def deserialize(channel_member: str) -> UUID:
    return UUID(channel_member)


async def add(
    channel_id: int,
    session_id: UUID,
) -> UUID:
    await clients.redis.sadd(
        make_key(channel_id),
        serialize(session_id),
    )
    return session_id


async def remove(
    channel_id: int,
    session_id: UUID,
) -> UUID | None:
    channel_key = make_key(channel_id)
    success = await clients.redis.srem(channel_key, serialize(session_id))
    return session_id if success == 1 else None


async def members(channel_id: int) -> set[UUID]:
    channel_key = make_key(channel_id)
    members = await clients.redis.smembers(channel_key)
    return {deserialize(member) for member in members}
