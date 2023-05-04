from server import clients


def make_key() -> str:
    return "server:last_match_id"


def serialize(match_id: int) -> str:
    return str(match_id)


def deserialize(match_id: str) -> int:
    return int(match_id)


async def claim_id() -> int:  # | None
    # try:
    async with await clients.redlock.lock("match_ids:lock"):
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
    # except LockError:
    #     return None

    return claimed_match_id
