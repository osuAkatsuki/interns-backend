from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import cast
from typing import Literal
from typing import TypedDict
from uuid import UUID

from app import clients


SESSION_EXPIRY = 60 * 60


def make_key(session_id: UUID | Literal["*"]) -> str:
    return f"server:sessions:{session_id}"


class Session(TypedDict):
    session_id: UUID
    account_id: int
    presence: Presence
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class Action:
    IDLE = 0
    AFK = 1
    PLAYING = 2
    EDITING = 3
    MODDING = 4
    MULTIPLAYER = 5
    WATCHING = 6
    UNKNOWN = 7
    TESTING = 8
    SUBMITTING = 9
    PAUSED = 10
    LOBBY = 11
    MULTIPLAYING = 12
    OSU_DIRECT = 13


class Presence(TypedDict):
    account_id: int
    username: str
    utc_offset: int
    country: str
    privileges: int
    game_mode: int
    latitude: float
    longitude: float
    action: int
    info_text: str
    beatmap_md5: str
    beatmap_id: int
    mods: int
    receive_match_updates: bool
    spectator_host_session_id: UUID | None
    away_message: str | None
    multiplayer_match_id: int | None
    last_communicated_at: datetime
    last_np_beatmap_id: int | None
    primary: bool


def serialize_presence(presence: Presence) -> str:
    return json.dumps(
        {
            "account_id": presence["account_id"],
            "username": presence["username"],
            "utc_offset": presence["utc_offset"],
            "country": presence["country"],
            "privileges": presence["privileges"],
            "game_mode": presence["game_mode"],
            "latitude": presence["latitude"],
            "longitude": presence["longitude"],
            "action": presence["action"],
            "info_text": presence["info_text"],
            "beatmap_md5": presence["beatmap_md5"],
            "beatmap_id": presence["beatmap_id"],
            "mods": presence["mods"],
            "receive_match_updates": presence["receive_match_updates"],
            "spectator_host_session_id": (
                str(presence["spectator_host_session_id"])
                if presence["spectator_host_session_id"] is not None
                else None
            ),
            "away_message": presence["away_message"],
            "multiplayer_match_id": presence["multiplayer_match_id"],
            "last_communicated_at": presence["last_communicated_at"].isoformat(),
            "last_np_beatmap_id": presence["last_np_beatmap_id"],
            "primary": presence["primary"],
        }
    )


def deserialize_presence(raw_presence: str) -> Presence:
    untyped_presence = json.loads(raw_presence)

    assert isinstance(untyped_presence, dict)

    untyped_presence["spectator_host_session_id"] = (
        UUID(untyped_presence["spectator_host_session_id"])
        if untyped_presence["spectator_host_session_id"] is not None
        else None
    )

    untyped_presence["last_communicated_at"] = datetime.fromisoformat(
        untyped_presence["last_communicated_at"]
    )

    return cast(Presence, untyped_presence)


def serialize(session: Session) -> str:
    return json.dumps(
        {
            "session_id": str(session["session_id"]),
            "account_id": session["account_id"],
            "presence": serialize_presence(session["presence"]),
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
    untyped_session["presence"] = deserialize_presence(untyped_session["presence"])
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
    presence: Presence,
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


async def fetch_primary_by_account_id(account_id: int) -> Session | None:
    all_sessions = await fetch_all()
    for session in all_sessions:
        if session["account_id"] == account_id and session["presence"]["primary"]:
            return session

    return None


async def fetch_primary_by_username(username: str) -> Session | None:
    sessions = await fetch_all()

    for session in sessions:
        if (
            session["presence"]["username"] == username
            and session["presence"]["primary"]
        ):
            return session

    return None


async def fetch_all_by_account_id(account_id: int) -> list[Session]:
    all_sessions = await fetch_all()
    sessions = []
    for session in all_sessions:
        if session["account_id"] == account_id:
            sessions.append(session)

    return sessions


async def fetch_all_by_username(username: str) -> list[Session]:
    all_sessions = await fetch_all()
    sessions = []
    for session in all_sessions:
        if session["presence"]["username"] == username:
            sessions.append(session)

    return sessions


async def fetch_all(
    has_any_privilege_bit: int | None = None,
) -> list[Session]:
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

            if (
                has_any_privilege_bit is not None
                and (session["presence"]["privileges"] & has_any_privilege_bit) == 0
            ):
                continue

            sessions.append(session)

    return sessions


async def partial_update(session_id: UUID, **kwargs: Any) -> Session | None:
    session_key = make_key(session_id)

    raw_session = await clients.redis.get(session_key)

    if raw_session is None:
        return None

    session = deserialize(raw_session)

    if not kwargs:
        return session

    expires_at = kwargs.get("expires_at")
    if expires_at is not None:
        expires_at = datetime.fromisoformat(expires_at)
        session["expires_at"] = expires_at

    # TODO: if we generalize sessions to be used for more than osu,
    # we need to adjust here because `presence=None` could be setting for real
    presence: Presence | None = kwargs.get("presence")
    if presence is not None:
        username = presence.get("username")
        if username is not None:
            session["presence"]["username"] = username

        privileges = presence.get("privileges")
        if privileges is not None:
            session["presence"]["privileges"] = privileges

        game_mode = presence.get("game_mode")
        if game_mode is not None:
            session["presence"]["game_mode"] = game_mode

        action = presence.get("action")
        if action is not None:
            session["presence"]["action"] = action

        info_text = presence.get("info_text")
        if info_text is not None:
            session["presence"]["info_text"] = info_text

        beatmap_md5 = presence.get("beatmap_md5")
        if beatmap_md5 is not None:
            session["presence"]["beatmap_md5"] = beatmap_md5

        beatmap_id = presence.get("beatmap_id")
        if beatmap_id is not None:
            session["presence"]["beatmap_id"] = beatmap_id

        mods = presence.get("mods")
        if mods is not None:
            session["presence"]["mods"] = mods

        game_mode = presence.get("game_mode")
        if game_mode is not None:
            session["presence"]["game_mode"] = game_mode

        receive_match_updates = presence.get("receive_match_updates")
        if receive_match_updates is not None:
            session["presence"]["receive_match_updates"] = receive_match_updates

        spectator_host_session_id = presence.get("spectator_host_session_id")
        if spectator_host_session_id is not None:
            session["presence"]["spectator_host_session_id"] = spectator_host_session_id

        away_message = presence.get("away_message")
        if away_message is not None:
            session["presence"]["away_message"] = away_message

        multiplayer_match_id = presence.get("multiplayer_match_id")
        if multiplayer_match_id is not None:
            session["presence"]["multiplayer_match_id"] = multiplayer_match_id

        last_communicated_at = presence.get("last_communicated_at")
        if last_communicated_at is not None:
            session["presence"]["last_communicated_at"] = last_communicated_at

        last_np_beatmap_id = presence.get("last_np_beatmap_id")
        if last_np_beatmap_id is not None:
            session["presence"]["last_np_beatmap_id"] = last_np_beatmap_id

        # primary cannot be updated

    session["updated_at"] = datetime.now()

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
