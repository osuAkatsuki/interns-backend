from datetime import datetime
from typing import cast
from typing import TypedDict

from server import clients

READ_PARAMS = """
    account_id,
    username,
    email_address,
    privileges,
    password,
    country,
    created_at,
    updated_at
"""


class Account(TypedDict):
    account_id: int
    username: str
    email_address: str
    privileges: int
    password: str
    country: str
    created_at: datetime
    updated_at: datetime


async def create(
    account_id: int,
    username: str,
    email_address: str,
    password: str,
    privileges: int,
    country: str,
) -> Account:
    account = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO accounts (account_id, username, email_address, password, privileges, country)
            VALUES (:account_id, :username, :email_address, :password, :privileges, :country)
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "username": username,
            "email_address": email_address,
            "password": password,
            "privileges": privileges,
            "country": country,
        },
    )

    assert account is not None
    return cast(Account, account)


async def fetch_many(
    privileges: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[Account]:
    accounts = await clients.database.fetch_all(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM accounts
            WHERE privileges = COALESCE(:privileges, privileges)
            LIMIT :limit
            OFFSET :offset
        """,
        values={
            "limit": page_size,
            "offset": (page - 1) * page_size,
            "privileges": privileges,
        },
    )
    return [cast(Account, account) for account in accounts]


async def fetch_by_account_id(account_id: int) -> Account | None:
    account = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM accounts
            WHERE account_id = :account_id
        """,
        values={"account_id": account_id},
    )
    return cast(Account, account) if account is not None else None


async def fetch_by_username(username: str) -> Account | None:
    account = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM accounts
            WHERE username = :username
        """,
        values={"username": username},
    )
    return cast(Account, account) if account is not None else None
