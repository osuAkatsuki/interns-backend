#!/usr/bin/env python3
import asyncio
import hashlib
import os

import bcrypt
import databases
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


def db_dsn(
    scheme: str,
    user: str,
    password: str,
    host: str,
    port: int,
    database: str,
) -> str:
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


database = databases.Database(
    db_dsn(
        scheme=os.environ["DB_SCHEME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        host="localhost",
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
)


def hash_password(plaintext_password: str) -> bytes:
    md5_password = hashlib.md5(plaintext_password.encode()).hexdigest()
    bcrypt_password = bcrypt.hashpw(
        password=md5_password.encode(),
        salt=bcrypt.gensalt(),
    )
    return bcrypt_password


async def main() -> int:
    async with database:
        account_id = await database.fetch_val(
            query="""\
                INSERT INTO accounts (username, email_address, privileges, password, country, created_at, updated_at)
                VALUES (:username, :email_address, :privileges, :password, :country, NOW(), NOW())
                RETURNING account_id
            """,
            values={
                "username": input("Username: "),
                "email_address": input("Email address: "),
                "privileges": 2_147_483_647,
                "password": hash_password(input("Password: ")).decode(),
                "country": input("Country: "),
            },
        )
        for game_mode in range(8):
            await database.execute(
                query="""\
                    INSERT INTO stats (account_id, game_mode)
                    VALUES (:account_id, :game_mode)
                """,
                values={
                    "account_id": account_id,
                    "game_mode": game_mode,
                },
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
