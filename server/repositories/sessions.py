from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import cast
from typing import Literal
from typing import TypedDict
from uuid import UUID

from server import clients


SESSION_EXPIRY = 60 * 60


def make_key(session_id: UUID | Literal["*"]) -> str:
    return f"server:sessions:{session_id}"


class Session(TypedDict):
    session_id: UUID
    account_id: int
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
    spectator_host_session_id: UUID | None


class _SerializablePresence(TypedDict):
    account_id: int
    username: str
    utc_offset: int
    country: str
    bancho_privileges: int
    game_mode: int
    latitude: float
    longitude: float
    action: int
    info_text: str
    beatmap_md5: str
    beatmap_id: int
    mods: int
    mode: int
    spectator_host_session_id: str | None


class _SerializableSession(TypedDict):
    session_id: str
    account_id: int
    presence: _SerializablePresence | None
    expires_at: str
    created_at: str
    updated_at: str


def serialize_presence(presence: Presence) -> _SerializablePresence:
    return {
        "account_id": presence["account_id"],
        "username": presence["username"],
        "utc_offset": presence["utc_offset"],
        "country": presence["country"],
        "bancho_privileges": presence["bancho_privileges"],
        "game_mode": presence["game_mode"],
        "latitude": presence["latitude"],
        "longitude": presence["longitude"],
        "action": presence["action"],
        "info_text": presence["info_text"],
        "beatmap_md5": presence["beatmap_md5"],
        "beatmap_id": presence["beatmap_id"],
        "mods": presence["mods"],
        "mode": presence["mode"],
        "spectator_host_session_id": (
            str(presence["spectator_host_session_id"])
            if presence["spectator_host_session_id"] is not None
            else None
        ),
    }


def serialize_session(session: Session) -> _SerializableSession:
    return {
        "session_id": str(session["session_id"]),
        "account_id": session["account_id"],
        "presence": (
            serialize_presence(session["presence"])
            if session["presence"] is not None
            else None
        ),
        "expires_at": session["expires_at"].isoformat(),
        "created_at": session["created_at"].isoformat(),
        "updated_at": session["updated_at"].isoformat(),
    }


def serialize(session: Session) -> str:
    return json.dumps(serialize_session(session))


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
) -> Session:
    now = datetime.now()
    expires_at = now + timedelta(seconds=SESSION_EXPIRY)
    session: Session = {
        "session_id": session_id,
        "account_id": account_id,
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


async def fetch_by_account_id(account_id: int) -> Session | None:
    all_sessions = await fetch_all(osu_clients_only=True)
    for session in all_sessions:
        if session["account_id"] == account_id:
            return session

    return None


async def fetch_by_username(username: str) -> Session | None:
    sessions = await fetch_all(osu_clients_only=True)

    for session in sessions:
        if session["presence"] is None:
            return None

        if session["presence"]["username"] == username:
            return session

    return None


async def fetch_all(osu_clients_only: bool = False) -> list[Session]:
    session_key = make_key("*")

    cursor = None
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


async def update_by_id(session_id: UUID, **kwargs: Any) -> Session | None:
    session_key = make_key(session_id)

    raw_session = await clients.redis.get(session_key)

    if raw_session is None:
        return None

    session = deserialize(raw_session)

    if not kwargs:
        return session

    session = dict(session)

    expires_at = kwargs.get("expires_at")
    if expires_at is not None:
        expires_at = datetime.fromisoformat(expires_at)
        session["expires_at"] = expires_at

    # TODO: can presences be removed from a session? None might be a valid state
    presence = kwargs.get("presence")
    if presence is not None:
        username = kwargs["presence"].get("username")
        if username is not None:
            session["presence"]["username"] = username

        bancho_privileges = kwargs["presence"].get("bancho_privileges")
        if bancho_privileges is not None:
            session["presence"]["bancho_privileges"] = bancho_privileges

        game_mode = kwargs["presence"].get("game_mode")
        if game_mode is not None:
            session["presence"]["game_mode"] = game_mode

        action = kwargs["presence"].get("action")
        if action is not None:
            session["presence"]["action"] = action

        info_text = kwargs["presence"].get("info_text")
        if info_text is not None:
            session["presence"]["info_text"] = info_text

        beatmap_md5 = kwargs["presence"].get("beatmap_md5")
        if beatmap_md5 is not None:
            session["presence"]["beatmap_md5"] = beatmap_md5

        beatmap_id = kwargs["presence"].get("beatmap_id")
        if beatmap_id is not None:
            session["presence"]["beatmap_id"] = beatmap_id

        mods = kwargs["presence"].get("mods")
        if mods is not None:
            session["presence"]["mods"] = mods

        mode = kwargs["presence"].get("mode")
        if mode is not None:
            session["presence"]["mode"] = mode

        spectator_host_session_id = kwargs["presence"].get("spectator_host_session_id")
        if spectator_host_session_id is not None:
            session["presence"]["spectator_host_session_id"] = spectator_host_session_id

    session["updated_at"] = datetime.now().isoformat()

    await clients.redis.set(session_key, serialize(session))

    if expires_at is not None:
        await clients.redis.expireat(session_key, expires_at)

    return cast(Session, session)


async def delete_by_id(session_id: UUID) -> Session | None:
    session_key = make_key(session_id)

    session = await clients.redis.get(session_key)
    if session is None:
        return None

    await clients.redis.delete(session_key)

    return deserialize(session)
