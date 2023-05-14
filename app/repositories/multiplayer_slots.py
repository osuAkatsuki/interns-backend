import json
from typing import cast
from typing import Literal
from typing import TypedDict

from app import clients


class MultiplayerSlot(TypedDict):
    slot_id: int
    account_id: int
    status: int  # enum
    team: int  # enum
    mods: int  # flags
    loaded: bool
    skipped: bool
    # TODO: i don't think we care about created & updated at here?
    # we will ideally be storing all events in a multiplayer_events
    # table in the database, which will hold the information


class SlotStatus:
    OPEN = 1
    LOCKED = 2
    NOT_READY = 4
    READY = 8
    NO_BEATMAP = 16
    PLAYING = 32
    COMPLETE = 64
    QUIT = 128

    # HAS_PLAYER = NOT_READY | READY | NO_BEATMAP | PLAYING | COMPLETE


def make_key(match_id: int, slot_id: int | Literal["*"]) -> str:
    return f"server:matches:{match_id}:slots:{slot_id}"


def serialize(slot: MultiplayerSlot) -> str:
    return json.dumps(
        {
            "slot_id": slot["slot_id"],
            "account_id": slot["account_id"],
            "status": slot["status"],
            "team": slot["team"],
            "mods": slot["mods"],
            "loaded": slot["loaded"],
            "skipped": slot["skipped"],
        }
    )


def deserialize(raw_slot: str) -> MultiplayerSlot:
    match = json.loads(raw_slot)

    assert isinstance(match, dict)

    return cast(MultiplayerSlot, match)


async def create(
    match_id: int,
    slot_id: int,
    account_id: int,
    status: int,
    team: int,
    mods: int,
    loaded: bool,
    skipped: bool,
) -> MultiplayerSlot:
    slot: MultiplayerSlot = {
        "slot_id": slot_id,
        "account_id": account_id,
        "status": status,
        "team": team,
        "mods": mods,
        "loaded": loaded,
        "skipped": skipped,
    }

    await clients.redis.set(
        name=make_key(match_id, slot_id),
        value=serialize(slot),
    )

    return slot


async def fetch_one(match_id: int, slot_id: int) -> MultiplayerSlot | None:
    raw_slot = await clients.redis.get(make_key(match_id, slot_id))
    if raw_slot is None:
        return None

    return deserialize(raw_slot)


async def fetch_all(match_id: int) -> list[MultiplayerSlot]:
    slot_key = make_key(match_id, "*")

    cursor = None
    slots = []

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=slot_key,
        )

        raw_slots = await clients.redis.mget(keys)

        for raw_slot in raw_slots:
            assert raw_slot is not None  # TODO: why does mget return list[T | None]?
            slot = deserialize(raw_slot)

            slots.append(slot)

    return slots


async def partial_update(
    match_id: int,
    slot_id: int,
    account_id: int | None,
    status: int | None,
    team: int | None,
    mods: int | None,
    loaded: bool | None,
    skipped: bool | None,
) -> MultiplayerSlot | None:
    slot = await fetch_one(match_id, slot_id)
    if slot is None:
        return None

    if account_id is not None:
        slot["account_id"] = account_id

    if status is not None:
        slot["status"] = status

    if team is not None:
        slot["team"] = team

    if mods is not None:
        slot["mods"] = mods

    if loaded is not None:
        slot["loaded"] = loaded

    if skipped is not None:
        slot["skipped"] = skipped

    await clients.redis.set(
        name=make_key(match_id, slot_id),
        value=serialize(slot),
    )

    return slot


async def delete(match_id: int, slot_id: int) -> MultiplayerSlot | None:
    slot_key = make_key(match_id, slot_id)

    raw_slot = await clients.redis.get(slot_key)

    if raw_slot is None:
        return None

    await clients.redis.delete(slot_key)

    return deserialize(raw_slot)


async def claim_slot_id(match_id: int) -> int | None:
    slots = await fetch_all(match_id)

    for slot in slots:
        if slot["account_id"] != 0:
            continue

        if slot["status"] != SlotStatus.OPEN:
            continue

        return slot["slot_id"]

    return None
