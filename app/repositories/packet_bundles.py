from datetime import datetime
from typing import cast
from typing import Literal
from typing import TypedDict
from uuid import UUID

from app import clients
from app import json
from app import logger


def make_key(osu_session_id: UUID | Literal["*"]) -> str:
    return f"server:packet-bundles:{osu_session_id}"


class PacketBundle(TypedDict):
    data: bytes
    created_at: datetime


def serialize(bundle: PacketBundle) -> bytes:
    return json.dumps(
        {
            "data": list(bundle["data"]),
            "created_at": bundle["created_at"].isoformat(),
        }
    )


def deserialize(raw_bundle: str) -> PacketBundle:
    untyped_bundle = json.loads(raw_bundle)
    untyped_bundle["created_at"] = datetime.fromisoformat(untyped_bundle["created_at"])
    return cast(PacketBundle, untyped_bundle)


async def enqueue(
    osu_session_id: UUID,
    data: bytes,
) -> PacketBundle:
    now = datetime.now()
    bundle: PacketBundle = {
        "data": data,
        "created_at": now,
    }

    queue_size = await clients.redis.rpush(
        make_key(osu_session_id),
        serialize(bundle),
    )

    # XXX: warn developers if a queue's size becomes very large
    if queue_size > 50:
        logger.warning(
            "Packet bundle size exceeded 20 items",
            queue_size=queue_size,
            osu_session_id=osu_session_id,
        )

    return bundle


async def dequeue_one(osu_session_id: UUID) -> PacketBundle | None:
    bundle = await clients.redis.lpop(make_key(osu_session_id))
    if bundle is None:
        return None

    return deserialize(bundle)


async def dequeue_all(osu_session_id: UUID) -> list[PacketBundle]:
    bundles = await clients.redis.lrange(
        make_key(osu_session_id),
        start=0,
        end=-1,
    )
    if bundles is None:
        return []

    await clients.redis.delete(make_key(osu_session_id))

    return [deserialize(bundle) for bundle in bundles]
