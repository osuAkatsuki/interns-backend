import hashlib
import uuid
from datetime import datetime
from uuid import UUID

from app import logger
from app import security
from app._typing import UNSET
from app._typing import Unset
from app.adapters import recaptcha
from app.errors import ServiceError
from app.repositories import accounts
from app.repositories import web_sessions
from app.repositories.web_sessions import WebSession


async def authenticate(
    username: str,
    password: str,
    recaptcha_token: str,
) -> WebSession | ServiceError:
    session_id = uuid.uuid4()
    try:
        if not await recaptcha.verify_recaptcha(recaptcha_token):
            return ServiceError.RECAPTCHA_VERIFICATION_FAILED

        account = await accounts.fetch_by_username(username)
        if account is None:
            return ServiceError.CREDENTIALS_NOT_FOUND

        # compensate for osu! password hashing
        password = hashlib.md5(password.encode()).hexdigest()

        if not security.check_password(password, account["password"].encode()):
            return ServiceError.CREDENTIALS_INCORRECT

        web_session = await web_sessions.create(
            session_id,
            account_id=account["account_id"],
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create web session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return web_session


async def fetch_by_id(web_session_id: UUID) -> WebSession | ServiceError:
    try:
        web_session = await web_sessions.fetch_by_id(web_session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch web session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if web_session is None:
        return ServiceError.WEB_SESSIONS_NOT_FOUND

    return web_session


async def fetch_many(
    page: int = 1,
    page_size: int = 50,
) -> list[WebSession] | ServiceError:
    try:
        _web_sessions = await web_sessions.fetch_many(
            page=page,
            page_size=page_size,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch web sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _web_sessions


async def fetch_total_count() -> int | ServiceError:
    try:
        count = await web_sessions.fetch_total_count()
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch web sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return count


async def fetch_all() -> list[WebSession] | ServiceError:
    try:
        _web_sessions = await web_sessions.fetch_all()
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch web sessions", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _web_sessions


async def partial_update(
    web_session_id: UUID,
    expires_at: datetime | Unset = UNSET,
) -> WebSession | ServiceError:
    try:
        web_session = await web_sessions.partial_update(
            web_session_id,
            expires_at=expires_at,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to update web session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if web_session is None:
        return ServiceError.WEB_SESSIONS_NOT_FOUND

    return web_session


async def delete_by_id(web_session_id: UUID) -> WebSession | ServiceError:
    try:
        web_session = await web_sessions.delete_by_id(web_session_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to delete web session", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if web_session is None:
        return ServiceError.WEB_SESSIONS_NOT_FOUND

    return web_session
