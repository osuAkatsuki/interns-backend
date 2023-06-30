import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from app import logger
from app.errors import ServiceError
from app.repositories import osu_sessions
from app.repositories.osu_sessions import OsuSession


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
    spectator_host_osu_session_id: UUID | None,
    away_message: str | None,
    multiplayer_match_id: int | None,
    last_communicated_at: datetime,
    last_np_beatmap_id: int | None,
    primary: bool,
) -> OsuSession | ServiceError:
    session_id = uuid.uuid4()

    try:
        session = await osu_sessions.create(
            session_id,
            account_id=account_id,
            username=username,
            action=action,
            away_message=away_message,
            beatmap_id=beatmap_id,
            beatmap_md5=beatmap_md5,
            country=country,
            game_mode=game_mode,
            info_text=info_text,
            last_communicated_at=last_communicated_at,
            last_np_beatmap_id=last_np_beatmap_id,
            latitude=latitude,
            longitude=longitude,
            mods=mods,
            multiplayer_match_id=multiplayer_match_id,
            pm_private=pm_private,
            primary=primary,
            privileges=privileges,
            receive_match_updates=receive_match_updates,
            spectator_host_osu_session_id=spectator_host_osu_session_id,
            utc_offset=utc_offset,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create osu! session", exc_info=exc)
        return ServiceError.OSU_SESSIONS_CREATE_FAILED

    return session


async def fetch_by_id(osu_session_id: UUID) -> OsuSession | ServiceError:
    try:
        osu_session = await osu_sessions.fetch_by_id(osu_session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch osu! session", exc_info=exc)
        return ServiceError.OSU_SESSIONS_FETCH_BY_ID_FAILED

    if osu_session is None:
        return ServiceError.OSU_SESSIONS_NOT_FOUND

    return osu_session


async def fetch_many(
    has_any_privilege_bit: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[OsuSession] | ServiceError:
    try:
        _osu_sessions = await osu_sessions.fetch_many(
            has_any_privilege_bit=has_any_privilege_bit,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.OSU_SESSIONS_FETCH_MANY_FAILED

    return _osu_sessions


async def fetch_total_count(
    has_any_privilege_bit: int | None = None,
) -> int | ServiceError:
    try:
        count = await osu_sessions.fetch_total_count(
            has_any_privilege_bit=has_any_privilege_bit,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.OSU_SESSIONS_FETCH_TOTAL_COUNT_FAILED

    return count


async def fetch_all(
    has_any_privilege_bit: int | None = None,
) -> list[OsuSession] | ServiceError:
    try:
        _osu_sessions = await osu_sessions.fetch_all(has_any_privilege_bit)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.OSU_SESSIONS_FETCH_ALL_FAILED

    return _osu_sessions


async def partial_update(
    osu_session_id: UUID, **kwargs: Any
) -> OsuSession | ServiceError:
    try:
        session = await osu_sessions.partial_update(osu_session_id, **kwargs)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to update osu! session", exc_info=exc)
        return ServiceError.OSU_SESSIONS_UPDATE_FAILED

    if session is None:
        return ServiceError.OSU_SESSIONS_NOT_FOUND

    return session


async def delete_by_id(osu_session_id: UUID) -> OsuSession | ServiceError:
    try:
        session = await osu_sessions.delete_by_id(osu_session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to delete osu! session", exc_info=exc)
        return ServiceError.OSU_SESSIONS_DELETE_FAILED

    if session is None:
        return ServiceError.OSU_SESSIONS_NOT_FOUND

    return session
