from typing import Literal
from uuid import UUID

from server import clients


def make_key(host_session_id: int | Literal["*"]) -> str:
    return f"server:spectators:{host_session_id}"


def serialize(session_id: UUID) -> str:
    return str(session_id)


def deserialize(host_session_id: bytes) -> UUID:
    return UUID(host_session_id.decode())


async def start_spectating(
    host_session_id: int,
    session_id: UUID,
) -> UUID:
    await clients.redis.sadd(
        make_key(host_session_id),
        serialize(session_id),
    )
    return session_id


async def stop_spectating(
    host_session_id: int,
    session_id: UUID,
) -> UUID | None:
    host_key = make_key(host_session_id)
    success = await clients.redis.srem(host_key, serialize(session_id))
    return session_id if success == 1 else None


async def all_spectators(host_session_id: int) -> set[UUID]:
    host_key = make_key(host_session_id)
    spectators = await clients.redis.smembers(host_key)
    return {deserialize(spectator) for spectator in spectators}
