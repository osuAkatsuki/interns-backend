#!/usr/bin/env python3
import asyncio
import hashlib
import sys
import os
from getpass import getpass

import bcrypt
import databases
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
mount_dir = os.path.join(script_dir, "..")
sys.path.append(mount_dir)

from server import validation, geolocation, security

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


DEFAULT_PRIVILEGES = (1 << 31) - 1  # big for now cuz full admin lol


async def main() -> int:
    while True:
        username = input("Username: ")
        if not validation.validate_username(username):
            print("Invalid Username! Retry!")
        else:
            break

    while True:
        email_address = input("Email address: ")
        if not validation.validate_email(email_address):
            print("Invalid Email! Retry!")
        else:
            break

    privileges = DEFAULT_PRIVILEGES

    while True:
        password = getpass("Password: ")
        if not validation.validate_password(password):
            print("Invalid Password! Retry!")
        else:
            break

    while True:
        country = input("Country: ")

        if geolocation.COUNTRY_STR_TO_INT.get(country) is None:
            print("Invalid Country! Retry!")
        else:
            break

    password = security.hash_password(password).decode()

    async with database:
        account_id = await database.fetch_val(
            query="""\
                INSERT INTO accounts (username, email_address, privileges, password, country, created_at, updated_at)
                VALUES (:username, :email_address, :privileges, :password, :country, NOW(), NOW())
                RETURNING account_id
            """,
            values={
                "username": username,
                "email_address": email_address,
                "privileges": privileges,
                "password": password,
                "country": country.upper(),
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
