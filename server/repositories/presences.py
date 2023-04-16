from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Literal
from uuid import UUID

from server import clients
from server import logger

PRESENCE_EXPIRY = 3600  # 1h


def create_presence_key(account_id: UUID | Literal["*"]) -> str:
    return f"users:presences:{account_id}"


async def create(
    account_id: UUID,
    username: str,
    utc_offset: int,
    country: str,
    bancho_privileges: int,
    game_mode: int,
    latitude: float,
    longitude: float,
    action: int,  # TODO: enum
    info_text: str,
    beatmap_md5: str,
    beatmap_id: int,
    mods: int,
    mode: int,
) -> dict[str, Any]:
    now = datetime.now()
    expires_at = now + timedelta(seconds=PRESENCE_EXPIRY)

    presence = {
        "account_id": account_id,
        "username": username,
        "utc_offset": utc_offset,
        "country": country,
        "bancho_privileges": bancho_privileges,
        "game_mode": game_mode,
        "latitude": latitude,
        "longitude": longitude,
        "action": action,
        "info_text": info_text,
        "beatmap_md5": beatmap_md5,
        "beatmap_id": beatmap_id,
        "mods": mods,
        "mode": mode,
        "expires_at": expires_at.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    await clients.redis.setex(
        name=create_presence_key(account_id),
        time=PRESENCE_EXPIRY,
        value=json.dumps(presence),
    )

    return presence


async def fetch_one(account_id: UUID) -> dict[str, Any] | None:
    presence = await clients.redis.get(create_presence_key(account_id))

    if presence is None:
        return None

    return json.loads(presence)


async def fetch_all() -> list[dict[str, Any]]:
    presence_key = create_presence_key("*")

    cursor, keys = await clients.redis.scan(
        cursor=0,
        match=presence_key,
    )

    presences = []
    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=presence_key,
        )

        raw_presences = await clients.redis.mget(keys)
        for presence in raw_presences:
            if presence is None:
                logger.warning("Session not found in Redis")
                continue

            presence = json.loads(presence)

            presences.append(presence)

    return presences


async def partial_update(
    account_id: UUID,
    **kwargs: Any,
) -> dict[str, Any] | None:
    raw_presence = await clients.redis.get(create_presence_key(account_id))

    if raw_presence is None:
        return None

    presence = json.loads(raw_presence)

    if not kwargs:
        return presence

    presence = dict(presence)

    expires_at: datetime | None = kwargs.get("expires_at")

    if expires_at is not None:
        presence["expires_at"] = expires_at.isoformat()

    presence["updated_at"] = datetime.now().isoformat()

    await clients.redis.set(
        create_presence_key(account_id),
        json.dumps(presence),
    )

    if expires_at is not None:
        await clients.redis.expireat(
            create_presence_key(account_id),
            expires_at,
        )

    return presence


async def delete(account_id: UUID) -> dict[str, Any] | None:
    presence_key = create_presence_key(account_id)

    presence = await clients.redis.get(presence_key)

    if presence is None:
        return None

    await clients.redis.delete(presence_key)

    return json.loads(presence)
