from datetime import datetime
from uuid import UUID
from uuid import uuid4

from app import logger
from app import security
from app.errors import ServiceError
from app.repositories import accounts
from app.repositories import sessions
from app.repositories.sessions import Session


async def create(
    username: str,
    password: str,
) -> Session | ServiceError:
    try:
        account = await accounts.fetch_by_username(username)
        if account is None:
            return ServiceError.CREDENTIALS_NOT_FOUND

        if not security.check_password(
            password=password,
            hashword=account["password"].encode(),
        ):
            return ServiceError.CREDENTIALS_INCORRECT

        session_id = uuid4()
        session = await sessions.create(
            session_id,
            account["account_id"],
            presence={
                "account_id": account["account_id"],
                "username": account["username"],
                "utc_offset": 0,  # TODO?
                "country": account["country"],
                "privileges": account["privileges"],
                "game_mode": 0,  # TODO?
                "latitude": 0.0,  # TODO?
                "longitude": 0.0,  # TODO?
                "action": 0,
                "info_text": "",
                "beatmap_md5": "",
                "beatmap_id": 0,
                "mods": 0,
                "receive_match_updates": False,
                "spectator_host_session_id": None,
                "away_message": None,
                "multiplayer_match_id": None,
                "last_communicated_at": datetime.now(),
                "last_np_beatmap_id": None,
            },
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return session


async def fetch_all() -> list[Session] | ServiceError:
    try:
        _sessions = await sessions.fetch_all()
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _sessions


async def fetch_one(session_id: UUID) -> Session | ServiceError:
    try:
        session = await sessions.fetch_by_id(session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if session is None:
        return ServiceError.SESSIONS_NOT_FOUND

    return session


async def delete(session_id: UUID) -> Session | ServiceError:
    try:
        session = await sessions.delete_by_id(session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to delete session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if session is None:
        return ServiceError.SESSIONS_NOT_FOUND

    return session
