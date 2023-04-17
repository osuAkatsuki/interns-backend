from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Literal
from uuid import UUID
from typing import TypedDict, cast


from server import clients


SESSION_EXPIRY = 60 * 60


def make_key(session_id: UUID | Literal["*"]) -> str:
    return f"server:sessions:{session_id}"


class Session(TypedDict):
    session_id: UUID
    account_id: int
    # user_agent: str
    presence: Presence | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class Presence(TypedDict):
    account_id: int
    username: str
    utc_offset: int
    country: str
    bancho_privileges: int
    game_mode: int
    latitude: float
    longitude: float
    action: int  # TODO: enum
    info_text: str
    beatmap_md5: str
    beatmap_id: int
    mods: int
    mode: int


def serialize(session: Mapping[str, Any]) -> str:
    return json.dumps(
        {
            "session_id": str(session["session_id"]),
            "account_id": session["account_id"],
            # "user_agent": session["user_agent"],
            "presence": {
                "account_id": session["presence"]["account_id"],
                "username": session["presence"]["username"],
                "utc_offset": session["presence"]["utc_offset"],
                "country": session["presence"]["country"],
                "bancho_privileges": session["presence"]["bancho_privileges"],
                "game_mode": session["presence"]["game_mode"],
                "latitude": session["presence"]["latitude"],
                "longitude": session["presence"]["longitude"],
                "action": session["presence"]["action"],
                "info_text": session["presence"]["info_text"],
                "beatmap_md5": session["presence"]["beatmap_md5"],
                "beatmap_id": session["presence"]["beatmap_id"],
                "mods": session["presence"]["mods"],
                "mode": session["presence"]["mode"],
            }
            if session["presence"] is not None
            else None,
            "expires_at": session["expires_at"].isoformat(),
            "created_at": session["created_at"].isoformat(),
            "updated_at": session["updated_at"].isoformat(),
        }
    )


def deserialize(raw_session: str) -> Session:
    untyped_session = json.loads(raw_session)

    assert isinstance(untyped_session, dict)

    untyped_session["session_id"] = UUID(untyped_session["session_id"])
    untyped_session["account_id"] = untyped_session["account_id"]
    untyped_session["expires_at"] = datetime.fromisoformat(
        untyped_session["expires_at"]
    )
    untyped_session["created_at"] = datetime.fromisoformat(
        untyped_session["created_at"]
    )
    untyped_session["updated_at"] = datetime.fromisoformat(
        untyped_session["updated_at"]
    )

    return cast(Session, untyped_session)


async def create(
    session_id: UUID,
    account_id: int,
    presence: Presence | None = None,
    # user_agent: str,
) -> Session:
    now = datetime.now()
    expires_at = now + timedelta(seconds=SESSION_EXPIRY)
    session: Session = {
        "session_id": session_id,
        "account_id": account_id,
        # "user_agent": user_agent,
        "presence": presence,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
    }

    await clients.redis.set(
        name=make_key(session_id),
        value=serialize(session),
        ex=SESSION_EXPIRY,
    )

    return session


async def fetch_by_id(session_id: UUID) -> Session | None:
    session_key = make_key(session_id)
    session = await clients.redis.get(session_key)
    return deserialize(session) if session is not None else None


async def fetch_all(osu_clients_only: bool = False) -> list[Session]:
    session_key = make_key("*")

    cursor, keys = await clients.redis.scan(
        cursor=0,
        match=session_key,
    )

    sessions = []

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=session_key,
        )

        raw_sessions = await clients.redis.mget(keys)

        for raw_session in raw_sessions:
            assert raw_session is not None  # TODO: why does mget return list[T | None]?
            session = deserialize(raw_session)

            if osu_clients_only and session["presence"] is None:
                continue

            sessions.append(session)

    return sessions


async def delete_by_id(session_id: UUID) -> Session | None:
    session_key = make_key(session_id)

    session = await clients.redis.get(session_key)
    if session is None:
        return None

    await clients.redis.delete(session_key)

    return deserialize(session)
