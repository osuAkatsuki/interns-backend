from aioredlock import Aioredlock, LockError, Sentinel

from server import settings, clients

# TODO: move this to global
lock_manager = Aioredlock(
    redis_connections=[(settings.REDIS_HOST, settings.REDIS_PORT)],  # type: ignore
)


def make_key() -> str:
    return "server:match_ids"  # TODO: is this weird?


def serialize(match_id: int) -> str:
    return str(match_id)


def deserialize(match_id: str) -> int:
    return int(match_id)


async def claim_id() -> int | None:
    try:
        async with await lock_manager.lock("match_ids:lock"):
            raw_match_id = await clients.redis.get(make_key())
            if raw_match_id is None:
                current_match_id = 1
            else:
                current_match_id = deserialize(raw_match_id)

            claimed_match_id = current_match_id + 1

            await clients.redis.set(
                name=make_key(),
                value=serialize(claimed_match_id),
            )
    except LockError:
        return None

    return claimed_match_id
