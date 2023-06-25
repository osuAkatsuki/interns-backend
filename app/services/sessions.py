from datetime import datetime

from typing import Any

from uuid import UUID
import uuid

from app import logger
from app.errors import ServiceError
from app.repositories import sessions
from app.repositories.sessions import Session
from app.repositories.sessions import Presence


async def create(
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
    spectator_host_session_id: UUID | None,
    away_message: str | None,
    multiplayer_match_id: int | None,
    last_communicated_at: datetime,
    last_np_beatmap_id: int | None,
    primary: bool,
) -> Session | ServiceError:
    session_id = uuid.uuid4()

    presence: Presence = {
        "account_id": account_id,
        "username": username,
        "action": action,
        "away_message": away_message,
        "beatmap_id": beatmap_id,
        "beatmap_md5": beatmap_md5,
        "country": country,
        "game_mode": game_mode,
        "info_text": info_text,
        "last_communicated_at": last_communicated_at,
        "last_np_beatmap_id": last_np_beatmap_id,
        "latitude": latitude,
        "longitude": longitude,
        "mods": mods,
        "multiplayer_match_id": multiplayer_match_id,
        "pm_private": pm_private,
        "primary": primary,
        "privileges": privileges,
        "receive_match_updates": receive_match_updates,
        "spectator_host_session_id": spectator_host_session_id,
        "utc_offset": utc_offset,
    }

    try:
        session = await sessions.create(
            session_id,
            account_id,
            presence,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create session", exc_info=exc)
        return ServiceError.SESSIONS_CREATE_FAILED

    return session


async def fetch_by_id(session_id: UUID) -> Session | ServiceError:
    try:
        session = await sessions.fetch_by_id(session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch session", exc_info=exc)
        return ServiceError.SESSIONS_FETCH_BY_ID_FAILED

    if session is None:
        return ServiceError.SESSIONS_NOT_FOUND

    return session


async def fetch_many(
    has_any_privilege_bit: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[Session] | ServiceError:
    try:
        _sessions = await sessions.fetch_many(
            has_any_privilege_bit=has_any_privilege_bit,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.SESSIONS_FETCH_MANY_FAILED

    return _sessions


async def fetch_total_count(
    has_any_privilege_bit: int | None = None,
) -> int | ServiceError:
    try:
        count = await sessions.fetch_total_count(
            has_any_privilege_bit=has_any_privilege_bit,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.SESSIONS_FETCH_TOTAL_COUNT_FAILED

    return count


async def fetch_all(
    has_any_privilege_bit: int | None = None,
) -> list[Session] | ServiceError:
    try:
        _sessions = await sessions.fetch_all(has_any_privilege_bit)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.SESSIONS_FETCH_ALL_FAILED

    return _sessions


async def partial_update(session_id: UUID, **kwargs: Any) -> Session | ServiceError:
    try:
        session = await sessions.partial_update(session_id, **kwargs)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to update session", exc_info=exc)
        return ServiceError.SESSIONS_UPDATE_FAILED

    if session is None:
        return ServiceError.SESSIONS_NOT_FOUND

    return session


async def delete_by_id(session_id: UUID) -> Session | ServiceError:
    try:
        session = await sessions.delete_by_id(session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to delete session", exc_info=exc)
        return ServiceError.SESSIONS_DELETE_FAILED

    if session is None:
        return ServiceError.SESSIONS_NOT_FOUND

    return session
