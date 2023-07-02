#!/usr/bin/env python3
import asyncio
import base64
import os
import ssl
import sys
from getpass import getpass

from dotenv import load_dotenv


script_dir = os.path.dirname(os.path.abspath(__file__))
mount_dir = os.path.join(script_dir, "..")
sys.path.append(mount_dir)

from app import geolocation
from app import security
from app import settings
from app import validation
from app.adapters import database as database_adapter
from app.game_modes import GameMode
from app.privileges import ServerPrivileges

load_dotenv(dotenv_path=".env")


database = database_adapter.Database(
    read_dsn=database_adapter.dsn(
        scheme=settings.READ_DB_SCHEME,
        user=settings.READ_DB_USER,
        password=settings.READ_DB_PASS,
        host=settings.READ_DB_HOST,
        port=settings.READ_DB_PORT,
        database=settings.READ_DB_NAME,
    ),
    read_db_ssl=(
        ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cadata=base64.b64decode(settings.READ_DB_CA_CERTIFICATE_BASE64).decode(),
        )
        if settings.READ_DB_USE_SSL
        else False
    ),
    write_dsn=database_adapter.dsn(
        scheme=settings.WRITE_DB_SCHEME,
        user=settings.WRITE_DB_USER,
        password=settings.WRITE_DB_PASS,
        host=settings.WRITE_DB_HOST,
        port=settings.WRITE_DB_PORT,
        database=settings.WRITE_DB_NAME,
    ),
    write_db_ssl=(
        ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cadata=base64.b64decode(settings.WRITE_DB_CA_CERTIFICATE_BASE64).decode(),
        )
        if settings.WRITE_DB_USE_SSL
        else False
    ),
    min_pool_size=settings.DB_POOL_MIN_SIZE,
    max_pool_size=settings.DB_POOL_MAX_SIZE,
)


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

    if settings.APP_ENV == "local":
        # give all privileges in development
        privileges = int("1" * 31, base=2)
    else:
        privileges = ServerPrivileges.UNRESTRICTED

    while True:
        password = getpass("Password: ")
        # TODO: turn this on once we're past initial dev stage?
        # if not validation.validate_password(password):
        #     print("Invalid Password! Retry!")
        # else:
        break

    while True:
        country = input("Country: ").upper()

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
                "country": country,
            },
        )
        for game_mode in [
            GameMode.VN_OSU,
            GameMode.VN_TAIKO,
            GameMode.VN_CATCH,
            GameMode.VN_MANIA,
            GameMode.RX_OSU,
            GameMode.RX_TAIKO,
            GameMode.RX_CATCH,
            GameMode.AP_OSU,
        ]:
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
    # use gnu readline interface
    import readline

    raise SystemExit(asyncio.run(main()))
