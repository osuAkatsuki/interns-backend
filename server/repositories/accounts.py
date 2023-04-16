from typing import Any
from uuid import UUID

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


# CREATE TABLE accounts (
# 	account_id SERIAL PRIMARY KEY,
# 	username TEXT NOT NULL,
# 	email_address TEXT NOT NULL,
# 	privileges INT NOT NULL,
# 	password TEXT NOT NULL,
# 	country TEXT NOT NULL,
#   created_at TIMESTAMPTZ NOT NULL,
#   updated_at TIMESTAMPTZ NOT NULL
# );
# CREATE UNIQUE INDEX ON accounts (username);
# CREATE UNIQUE INDEX ON accounts (email_address);


async def create(
    account_id: UUID,
    username: str,
    email_address: str,
    password: str,
    privileges: int,
    country: str,
) -> dict[str, Any]:
    account = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO accounts (account_id, username, email_address, password, privileges, country)
            VALUES (:account_id, :username, :email_address, :password, :privileges, :country)
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "username": username,
            "email": email_address,
            "password": password,
            "privileges": privileges,
            "country": country,
        },
    )

    assert account is not None
    return dict(account._mapping)


async def fetch_many(
    privileges: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[dict[str, Any]]:
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
    return [dict(account._mapping) for account in accounts]


async def fetch_by_account_id(account_id: UUID) -> dict[str, Any] | None:
    account = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM accounts
            WHERE account_id = :account_id
        """,
        values={"account_id": account_id},
    )
    return dict(account._mapping) if account is not None else None


async def fetch_by_username(username: str) -> dict[str, Any] | None:
    account = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM accounts
            WHERE username = :username
        """,
        values={"username": username},
    )
    return dict(account._mapping) if account is not None else None
