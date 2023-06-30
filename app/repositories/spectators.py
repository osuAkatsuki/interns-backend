from typing import Literal
from uuid import UUID

from app import clients


def make_key(host_osu_session_id: UUID | Literal["*"]) -> str:
    return f"server:spectators:{host_osu_session_id}"


def serialize(osu_session_id: UUID) -> str:
    return str(osu_session_id)


def deserialize(host_osu_session_id: bytes) -> UUID:
    return UUID(host_osu_session_id.decode())


async def add(
    host_osu_session_id: UUID,
    osu_session_id: UUID,
) -> UUID:
    await clients.redis.sadd(
        make_key(host_osu_session_id),
        serialize(osu_session_id),
    )
    return osu_session_id


async def remove(
    host_osu_session_id: UUID,
    osu_session_id: UUID,
) -> UUID | None:
    host_key = make_key(host_osu_session_id)
    success = await clients.redis.srem(host_key, serialize(osu_session_id))
    return osu_session_id if success == 1 else None


async def members(host_osu_session_id: UUID) -> set[UUID]:
    host_key = make_key(host_osu_session_id)
    spectators = await clients.redis.smembers(host_key)
    return {deserialize(spectator) for spectator in spectators}
