from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients
from app.typing import UNSET
from app.typing import Unset

READ_PARAMS = """
    account_id,
    username,
    email_address,
    privileges,
    password,
    country,
    silence_end,
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
    silence_end: datetime | None
    created_at: datetime
    updated_at: datetime


class AccountUpdateFields(TypedDict, total=False):
    username: str
    email_address: str
    privileges: int
    password: str
    country: str
    silence_end: datetime | None


async def create(
    username: str,
    email_address: str,
    password: str,
    privileges: int,
    country: str,
) -> Account:
    account = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO accounts (username, email_address, password, privileges, country)
            VALUES (:username, :email_address, :password, :privileges, :country)
            RETURNING {READ_PARAMS}
        """,
        values={
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
            "privileges": privileges,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )
    return cast(list[Account], accounts)


async def fetch_total_count(
    privileges: int | None = None,
) -> int:
    rec = await clients.database.fetch_one(
        query=f"""\
            SELECT COUNT(*) AS count
            FROM accounts
            WHERE privileges = COALESCE(:privileges, privileges)
        """,
        values={
            "privileges": privileges,
        },
    )
    assert rec is not None
    return rec["count"]


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


async def partial_update(
    account_id: int,
    username: str | Unset = UNSET,
    email_address: str | Unset = UNSET,
    privileges: int | Unset = UNSET,
    password: str | Unset = UNSET,
    country: str | Unset = UNSET,
    silence_end: datetime | None | Unset = UNSET,
) -> Account | None:
    update_fields: AccountUpdateFields = {}
    if not isinstance(username, Unset):
        update_fields["username"] = username
    if not isinstance(email_address, Unset):
        update_fields["email_address"] = email_address
    if not isinstance(privileges, Unset):
        update_fields["privileges"] = privileges
    if not isinstance(password, Unset):
        update_fields["password"] = password
    if not isinstance(country, Unset):
        update_fields["country"] = country
    if not isinstance(silence_end, Unset):
        update_fields["silence_end"] = silence_end

    query = f"""\
        UPDATE accounts
           SET {", ".join(f"{k} = :{k}" for k in update_fields)},
               updated_at = NOW()
         WHERE account_id = :account_id
     RETURNING {READ_PARAMS}
    """
    values = {"account_id": account_id} | update_fields

    account = await clients.database.fetch_one(query, values)
    return cast(Account, account) if account is not None else None
