from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients
from app.undefined import Undefined, UndefinedType

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
    username: str | UndefinedType = Undefined,
    email_address: str | UndefinedType = Undefined,
    privileges: int | UndefinedType = Undefined,
    password: str | UndefinedType = Undefined,
    country: str | UndefinedType = Undefined,
    silence_end: datetime | None | UndefinedType = Undefined,
) -> Account | None:
    update_fields = {}
    if username is not Undefined:
        update_fields["username"] = username
    if email_address is not Undefined:
        update_fields["email_address"] = email_address
    if privileges is not Undefined:
        update_fields["privileges"] = privileges
    if password is not Undefined:
        update_fields["password"] = password
    if country is not Undefined:
        update_fields["country"] = country
    if silence_end is not Undefined:
        update_fields["silence_end"] = silence_end

    updates = [f"{k} = :{k}" for k in update_fields.keys()]
    query = (
        "UPDATE accounts SET " + ','.join(updates) +
        " WHERE account_id = :account_id "
        f"RETURNING {READ_PARAMS}"
    )

    account = await clients.database.fetch_one(
        query=query,
        values={"account_id": account_id} | update_fields,
    )

    return cast(Account, account) if account is not None else None
