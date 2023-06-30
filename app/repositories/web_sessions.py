from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from typing import cast
from typing import Literal
from typing import TypedDict
from uuid import UUID

from app import clients
from app._typing import UNSET
from app._typing import Unset


WEB_SESSION_TTL = 60 * 60 * 24  # 24 hours


def make_key(web_session_id: UUID | Literal["*"]) -> str:
    return f"server:web_sessions:{web_session_id}"


class WebSession(TypedDict):
    web_session_id: UUID
    account_id: int
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


def serialize(web_session: WebSession) -> str:
    return json.dumps(
        {
            "web_session_id": str(web_session["web_session_id"]),
            "account_id": web_session["account_id"],
            "expires_at": web_session["expires_at"].isoformat(),
            "created_at": web_session["created_at"].isoformat(),
            "updated_at": web_session["updated_at"].isoformat(),
        }
    )


def deserialize(raw_session: str) -> WebSession:
    untyped_session = json.loads(raw_session)

    assert isinstance(untyped_session, dict)

    untyped_session["web_session_id"] = UUID(untyped_session["web_session_id"])
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

    return cast(WebSession, untyped_session)


async def create(
    web_session_id: UUID,
    account_id: int,
) -> WebSession:
    now = datetime.now()
    expires_at = now + timedelta(seconds=WEB_SESSION_TTL)
    web_session: WebSession = {
        "web_session_id": web_session_id,
        "account_id": account_id,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
    }

    await clients.redis.set(
        name=make_key(web_session_id),
        value=serialize(web_session),
        ex=WEB_SESSION_TTL,
    )

    return web_session


async def fetch_by_id(web_session_id: UUID) -> WebSession | None:
    web_session_key = make_key(web_session_id)
    web_session = await clients.redis.get(web_session_key)
    return deserialize(web_session) if web_session is not None else None


async def fetch_by_account_id(account_id: int) -> WebSession | None:
    all_web_sessions = await fetch_all()
    for web_session in all_web_sessions:
        if web_session["account_id"] == account_id:
            return web_session

    return None


async def fetch_many(
    page: int = 1,
    page_size: int = 50,
) -> list[WebSession]:
    web_session_key = make_key("*")

    web_sessions = []

    _, keys = await clients.redis.scan(
        cursor=page_size * (page - 1),
        count=page_size,
        match=web_session_key,
    )

    raw_web_sessions = await clients.redis.mget(keys)

    for raw_web_session in raw_web_sessions:
        assert raw_web_session is not None  # TODO: why does mget return list[T | None]?
        web_session = deserialize(raw_web_session)

        web_sessions.append(web_session)

    return web_sessions


async def fetch_total_count() -> int:
    web_session_key = make_key("*")

    cursor = None
    count = 0

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=web_session_key,
        )
        count += len(keys)

    return count


async def fetch_all() -> list[WebSession]:
    web_session_key = make_key("*")

    cursor = None
    web_sessions = []

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=web_session_key,
        )

        raw_web_sessions = await clients.redis.mget(keys)

        for raw_web_session in raw_web_sessions:
            assert (
                raw_web_session is not None
            )  # TODO: why does mget return list[T | None]?

            web_session = deserialize(raw_web_session)

            web_sessions.append(web_session)

    return web_sessions


async def partial_update(
    web_session_id: UUID,
    expires_at: datetime | Unset = UNSET,
) -> WebSession | None:
    web_session_key = make_key(web_session_id)

    raw_web_session = await clients.redis.get(web_session_key)

    if raw_web_session is None:
        return None

    web_session = deserialize(raw_web_session)

    if not isinstance(expires_at, Unset):
        web_session["expires_at"] = expires_at
        await clients.redis.expireat(web_session_key, expires_at)

    web_session["updated_at"] = datetime.now()

    await clients.redis.set(web_session_key, serialize(web_session))

    return cast(WebSession, web_session)


async def delete_by_id(web_session_id: UUID) -> WebSession | None:
    session_key = make_key(web_session_id)

    web_session = await clients.redis.get(session_key)
    if web_session is None:
        return None

    await clients.redis.delete(session_key)

    return deserialize(web_session)
