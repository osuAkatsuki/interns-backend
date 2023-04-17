from datetime import datetime
from typing import Any
from typing import TypedDict
from typing import Literal
from uuid import UUID

from server import json
from server import clients
from server import logger
from typing import cast


def make_key(session_id: UUID | Literal["*"]) -> str:
    return f"server:packet-bundles:{session_id}"


class PacketBundle(TypedDict):
    data: list[int]
    created_at: datetime


def serialize(data: list[int]) -> bytes:
    now = datetime.now()
    bundle = {
        "data": data,
        "created_at": now.isoformat(),
    }
    return json.dumps(bundle)


def deserialize(data: str) -> PacketBundle:
    raw_bundle = json.loads(data)
    raw_bundle["created_at"] = datetime.fromisoformat(raw_bundle["created_at"])
    return cast(PacketBundle, raw_bundle)


async def enqueue(
    session_id: UUID,
    data: list[int],
) -> PacketBundle:
    now = datetime.now()
    bundle: PacketBundle = {
        "data": data,
        "created_at": now,
    }

    # XXX: warn developers if a queue's size becomes very large
    queue_size = await clients.redis.rpush(
        make_key(session_id),
        json.dumps(bundle),
    )
    if queue_size > 50:
        logger.warning(
            "Packet bundle size exceeded 20 items",
            queue_size=queue_size,
            session_id=session_id,
        )

    return bundle


async def dequeue_one(session_id: UUID) -> PacketBundle | None:
    bundle = await clients.redis.lpop(make_key(session_id))
    if bundle is None:
        return None

    return json.loads(bundle)


async def dequeue_all(session_id: UUID) -> list[dict[str, Any]]:
    bundles = await clients.redis.lrange(
        make_key(session_id),
        start=0,
        end=-1,
    )
    if bundles is None:
        return []

    await clients.redis.delete(make_key(session_id))

    return [json.loads(bundle) for bundle in bundles]
