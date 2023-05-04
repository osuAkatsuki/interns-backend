from datetime import datetime
from typing import Any
from typing import cast
from typing import TypedDict

from server import clients


READ_PARAMS = """\
    login_attempt_id,
    successful,
    ip_address,
    user_agent,
    created_at
"""


class Login_Attempt(TypedDict):
    login_attempt_id: int
    successful: bool
    ip_address: str
    user_agent: str
    created_at: datetime


async def create(
    login_attempt_id: int,
    successful: bool,
    ip_address: str,
    user_agent: str,
) -> Login_Attempt:
    login_attempt = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO login_attempts (login_attempt_id, successful, ip_address, user_agent)
            VALUES (:login_attempt_id, :successful, :ip_address, :user_agent)
            RETURNING {READ_PARAMS}
        """,
        values={
            "login_attempt_id": login_attempt_id,
            "successful": successful,
            "ip_address": ip_address,
            "user_agent": user_agent,
        },
    )

    assert login_attempt is not None
    return cast(Login_Attempt, login_attempt)


async def fetch_one(login_attempt_id: int) -> Login_Attempt | None:
    login_attempt = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM login_attempts
            WHERE login_attempt_id = :login_attempt_id
        """,
        values={
            "login_attempt_id": login_attempt_id,
        },
    )
    return cast(Login_Attempt, login_attempt) if login_attempt is not None else None


async def fetch_many(
    successful: bool | None,
    ip_address: str | None,
    user_agent: str | None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[Login_Attempt] | None:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM login_attempts
        WHERE login_attempt_id = COALESCE(:successful, successful)
        AND ip_address = COALESCE(:ip_address, ip_address)
        AND user_agent = COALESCE(:user_agent user_agent)
    """
    values = {
        "successful": successful,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    if page is not None and page_size is not None:
        query += f"""\
            LIMIT :page_size
            OFFSET :offset
        """
        values["limit"] = page_size
        values["offset"] = (page - 1) * page_size

    login_attempt = await clients.database.fetch_all(query, values)
    return [cast(Login_Attempt, login_attempt) for attempt in login_attempt]
