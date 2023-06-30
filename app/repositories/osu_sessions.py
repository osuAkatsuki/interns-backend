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


OSU_SESSION_TTL = 60 * 60  # 1 hour


def make_key(osu_session_id: UUID | Literal["*"]) -> str:
    return f"server:osu_sessions:{osu_session_id}"


class OsuSession(TypedDict):
    osu_session_id: UUID
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
    pm_private: bool
    receive_match_updates: bool
    spectator_host_osu_session_id: UUID | None
    away_message: str | None
    multiplayer_match_id: int | None
    last_communicated_at: datetime
    last_np_beatmap_id: int | None
    primary: bool
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


def serialize(osu_session: OsuSession) -> str:
    return json.dumps(
        {
            "osu_session_id": str(osu_session["osu_session_id"]),
            "account_id": osu_session["account_id"],
            "username": osu_session["username"],
            "utc_offset": osu_session["utc_offset"],
            "country": osu_session["country"],
            "privileges": osu_session["privileges"],
            "game_mode": osu_session["game_mode"],
            "latitude": osu_session["latitude"],
            "longitude": osu_session["longitude"],
            "action": osu_session["action"],
            "info_text": osu_session["info_text"],
            "beatmap_md5": osu_session["beatmap_md5"],
            "beatmap_id": osu_session["beatmap_id"],
            "mods": osu_session["mods"],
            "pm_private": osu_session["pm_private"],
            "receive_match_updates": osu_session["receive_match_updates"],
            "spectator_host_osu_session_id": (
                str(osu_session["spectator_host_osu_session_id"])
                if osu_session["spectator_host_osu_session_id"] is not None
                else None
            ),
            "away_message": osu_session["away_message"],
            "multiplayer_match_id": osu_session["multiplayer_match_id"],
            "last_communicated_at": osu_session["last_communicated_at"].isoformat(),
            "last_np_beatmap_id": osu_session["last_np_beatmap_id"],
            "primary": osu_session["primary"],
            "expires_at": osu_session["expires_at"].isoformat(),
            "created_at": osu_session["created_at"].isoformat(),
            "updated_at": osu_session["updated_at"].isoformat(),
        }
    )


def deserialize(raw_session: str) -> OsuSession:
    untyped_session = json.loads(raw_session)

    assert isinstance(untyped_session, dict)

    untyped_session["osu_session_id"] = UUID(untyped_session["osu_session_id"])
    untyped_session["account_id"] = untyped_session["account_id"]

    untyped_session["spectator_host_osu_session_id"] = (
        UUID(untyped_session["spectator_host_osu_session_id"])
        if untyped_session["spectator_host_osu_session_id"] is not None
        else None
    )

    untyped_session["last_communicated_at"] = datetime.fromisoformat(
        untyped_session["last_communicated_at"]
    )

    untyped_session["expires_at"] = datetime.fromisoformat(
        untyped_session["expires_at"]
    )
    untyped_session["created_at"] = datetime.fromisoformat(
        untyped_session["created_at"]
    )
    untyped_session["updated_at"] = datetime.fromisoformat(
        untyped_session["updated_at"]
    )

    return cast(OsuSession, untyped_session)


async def create(
    osu_session_id: UUID,
    account_id: int,
    username: str,
    utc_offset: int,
    country: str,
    privileges: int,
    game_mode: int,
    latitude: float,
    longitude: float,
    action: int,
    info_text: str,
    beatmap_md5: str,
    beatmap_id: int,
    mods: int,
    pm_private: bool,
    receive_match_updates: bool,
    spectator_host_osu_session_id: UUID | None,
    away_message: str | None,
    multiplayer_match_id: int | None,
    last_communicated_at: datetime,
    last_np_beatmap_id: int | None,
    primary: bool,
) -> OsuSession:
    now = datetime.now()
    expires_at = now + timedelta(seconds=OSU_SESSION_TTL)
    osu_session: OsuSession = {
        "osu_session_id": osu_session_id,
        "account_id": account_id,
        "username": username,
        "utc_offset": utc_offset,
        "country": country,
        "privileges": privileges,
        "game_mode": game_mode,
        "latitude": latitude,
        "longitude": longitude,
        "action": action,
        "info_text": info_text,
        "beatmap_md5": beatmap_md5,
        "beatmap_id": beatmap_id,
        "mods": mods,
        "pm_private": pm_private,
        "receive_match_updates": receive_match_updates,
        "spectator_host_osu_session_id": spectator_host_osu_session_id,
        "away_message": away_message,
        "multiplayer_match_id": multiplayer_match_id,
        "last_communicated_at": last_communicated_at,
        "last_np_beatmap_id": last_np_beatmap_id,
        "primary": primary,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
    }

    await clients.redis.set(
        name=make_key(osu_session_id),
        value=serialize(osu_session),
        ex=OSU_SESSION_TTL,
    )

    return osu_session


async def fetch_by_id(osu_session_id: UUID) -> OsuSession | None:
    osu_session_key = make_key(osu_session_id)
    osu_session = await clients.redis.get(osu_session_key)
    return deserialize(osu_session) if osu_session is not None else None


async def fetch_primary_by_account_id(account_id: int) -> OsuSession | None:
    all_osu_sessions = await fetch_all()
    for osu_session in all_osu_sessions:
        if osu_session["account_id"] == account_id and osu_session["primary"]:
            return osu_session

    return None


async def fetch_primary_by_username(username: str) -> OsuSession | None:
    osu_sessions = await fetch_all()

    for osu_session in osu_sessions:
        if osu_session["username"] == username and osu_session["primary"]:
            return osu_session

    return None


async def fetch_many(
    has_any_privilege_bit: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[OsuSession]:
    osu_session_key = make_key("*")

    osu_sessions = []

    _, keys = await clients.redis.scan(
        cursor=page_size * (page - 1),
        count=page_size,
        match=osu_session_key,
    )

    raw_osu_sessions = await clients.redis.mget(keys)

    for raw_osu_session in raw_osu_sessions:
        assert raw_osu_session is not None  # TODO: why does mget return list[T | None]?
        osu_session = deserialize(raw_osu_session)

        if (
            has_any_privilege_bit not in (None, 0)
            and (osu_session["privileges"] & has_any_privilege_bit) == 0
        ):
            continue

        osu_sessions.append(osu_session)

    return osu_sessions


async def fetch_total_count(has_any_privilege_bit: int | None = None) -> int:
    osu_session_key = make_key("*")

    cursor = None
    count = 0

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=osu_session_key,
        )

        raw_osu_sessions = await clients.redis.mget(keys)

        for raw_osu_session in raw_osu_sessions:
            assert (
                raw_osu_session is not None
            )  # TODO: why does mget return list[T | None]?
            osu_session = deserialize(raw_osu_session)

            if (
                has_any_privilege_bit not in (None, 0)
                and (osu_session["privileges"] & has_any_privilege_bit) == 0
            ):
                continue

            count += 1

    return count


async def fetch_all_by_account_id(account_id: int) -> list[OsuSession]:
    all_osu_sessions = await fetch_all()
    osu_sessions = []
    for osu_session in all_osu_sessions:
        if osu_session["account_id"] == account_id:
            osu_sessions.append(osu_session)

    return osu_sessions


async def fetch_all_by_username(username: str) -> list[OsuSession]:
    all_osu_sessions = await fetch_all()
    osu_sessions = []
    for osu_session in all_osu_sessions:
        if osu_session["username"] == username:
            osu_sessions.append(osu_session)

    return osu_sessions


async def fetch_all(has_any_privilege_bit: int | None = None) -> list[OsuSession]:
    osu_session_key = make_key("*")

    cursor = None
    osu_sessions = []

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=osu_session_key,
        )

        raw_osu_sessions = await clients.redis.mget(keys)

        for raw_osu_session in raw_osu_sessions:
            assert (
                raw_osu_session is not None
            )  # TODO: why does mget return list[T | None]?
            osu_session = deserialize(raw_osu_session)

            if (
                has_any_privilege_bit not in (None, 0)
                and (osu_session["privileges"] & has_any_privilege_bit) == 0
            ):
                continue

            osu_sessions.append(osu_session)

    return osu_sessions


from app._typing import Unset, UNSET


async def partial_update(
    osu_session_id: UUID,
    username: str | Unset = UNSET,
    utc_offset: int | Unset = UNSET,
    country: str | Unset = UNSET,
    privileges: int | Unset = UNSET,
    game_mode: int | Unset = UNSET,
    latitude: float | Unset = UNSET,
    longitude: float | Unset = UNSET,
    action: int | Unset = UNSET,
    info_text: str | Unset = UNSET,
    beatmap_md5: str | Unset = UNSET,
    beatmap_id: int | Unset = UNSET,
    mods: int | Unset = UNSET,
    pm_private: bool | Unset = UNSET,
    receive_match_updates: bool | Unset = UNSET,
    spectator_host_osu_session_id: UUID | None | Unset = UNSET,
    away_message: str | None | Unset = UNSET,
    multiplayer_match_id: int | None | Unset = UNSET,
    last_communicated_at: datetime | Unset = UNSET,
    last_np_beatmap_id: int | None | Unset = UNSET,
    expires_at: datetime | Unset = UNSET,
) -> OsuSession | None:
    osu_session_key = make_key(osu_session_id)

    raw_osu_session = await clients.redis.get(osu_session_key)

    if raw_osu_session is None:
        return None

    osu_session = deserialize(raw_osu_session)

    if not isinstance(username, Unset):
        osu_session["username"] = username
    if not isinstance(utc_offset, Unset):
        osu_session["utc_offset"] = utc_offset
    if not isinstance(country, Unset):
        osu_session["country"] = country
    if not isinstance(privileges, Unset):
        osu_session["privileges"] = privileges
    if not isinstance(game_mode, Unset):
        osu_session["game_mode"] = game_mode
    if not isinstance(latitude, Unset):
        osu_session["latitude"] = latitude
    if not isinstance(longitude, Unset):
        osu_session["longitude"] = longitude
    if not isinstance(action, Unset):
        osu_session["action"] = action
    if not isinstance(info_text, Unset):
        osu_session["info_text"] = info_text
    if not isinstance(beatmap_md5, Unset):
        osu_session["beatmap_md5"] = beatmap_md5
    if not isinstance(beatmap_id, Unset):
        osu_session["beatmap_id"] = beatmap_id
    if not isinstance(mods, Unset):
        osu_session["mods"] = mods
    if not isinstance(pm_private, Unset):
        osu_session["pm_private"] = pm_private
    if not isinstance(receive_match_updates, Unset):
        osu_session["receive_match_updates"] = receive_match_updates
    if not isinstance(spectator_host_osu_session_id, Unset):
        osu_session["spectator_host_osu_session_id"] = spectator_host_osu_session_id
    if not isinstance(away_message, Unset):
        osu_session["away_message"] = away_message
    if not isinstance(multiplayer_match_id, Unset):
        osu_session["multiplayer_match_id"] = multiplayer_match_id
    if not isinstance(last_communicated_at, Unset):
        osu_session["last_communicated_at"] = last_communicated_at
    if not isinstance(last_np_beatmap_id, Unset):
        osu_session["last_np_beatmap_id"] = last_np_beatmap_id
    # (primary cannot be updated)
    if not isinstance(expires_at, Unset):
        osu_session["expires_at"] = expires_at
        await clients.redis.expireat(osu_session_key, expires_at)

    osu_session["updated_at"] = datetime.now()

    await clients.redis.set(osu_session_key, serialize(osu_session))

    return cast(OsuSession, osu_session)


async def delete_by_id(session_id: UUID) -> OsuSession | None:
    session_key = make_key(session_id)

    session = await clients.redis.get(session_key)
    if session is None:
        return None

    await clients.redis.delete(session_key)

    return deserialize(session)
