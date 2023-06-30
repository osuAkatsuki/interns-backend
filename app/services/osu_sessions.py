import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from app import logger
from app._typing import UNSET
from app._typing import Unset
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
        osu_session = await osu_sessions.create(
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
        return ServiceError.INTERNAL_SERVER_ERROR

    return osu_session


async def fetch_by_id(osu_session_id: UUID) -> OsuSession | ServiceError:
    try:
        osu_session = await osu_sessions.fetch_by_id(osu_session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch osu! session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

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
        logger.error("Failed to fetch osu! sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _osu_sessions


async def fetch_total_count(
    has_any_privilege_bit: int | None = None,
) -> int | ServiceError:
    try:
        count = await osu_sessions.fetch_total_count(
            has_any_privilege_bit=has_any_privilege_bit,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch osu! sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return count


async def fetch_all(
    has_any_privilege_bit: int | None = None,
) -> list[OsuSession] | ServiceError:
    try:
        _osu_sessions = await osu_sessions.fetch_all(has_any_privilege_bit)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch osu! sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _osu_sessions


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
) -> OsuSession | ServiceError:
    try:
        osu_session = await osu_sessions.partial_update(
            osu_session_id,
            username=username,
            utc_offset=utc_offset,
            country=country,
            privileges=privileges,
            game_mode=game_mode,
            latitude=latitude,
            longitude=longitude,
            action=action,
            info_text=info_text,
            beatmap_md5=beatmap_md5,
            beatmap_id=beatmap_id,
            mods=mods,
            pm_private=pm_private,
            receive_match_updates=receive_match_updates,
            spectator_host_osu_session_id=spectator_host_osu_session_id,
            away_message=away_message,
            multiplayer_match_id=multiplayer_match_id,
            last_communicated_at=last_communicated_at,
            last_np_beatmap_id=last_np_beatmap_id,
            expires_at=expires_at,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to update osu! session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if osu_session is None:
        return ServiceError.OSU_SESSIONS_NOT_FOUND

    return osu_session


async def delete_by_id(osu_session_id: UUID) -> OsuSession | ServiceError:
    try:
        osu_session = await osu_sessions.delete_by_id(osu_session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to delete osu! session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if osu_session is None:
        return ServiceError.OSU_SESSIONS_NOT_FOUND

    return osu_session
