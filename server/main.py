#!/usr/bin/env python3
from typing import Any
from uuid import uuid4

from server import security
import redis.asyncio
from server import geolocation

from databases import Database
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from server import logger

from server import clients
from server import packets
from server import privileges
from server import settings
from server.repositories import accounts
from server.repositories import channels
from server.repositories import sessions
from server.repositories import presences
from server.repositories import stats

app = FastAPI()


@app.get("/")
async def home_page():
    return "Hello, world!"


def db_dsn(
    scheme: str,
    user: str,
    passwd: str,
    host: str,
    port: int,
    database: str,
) -> str:
    return f"{scheme}://{user}:{passwd}@{host}:{port}/{database}"


@app.on_event("startup")
async def start_database():
    logger.info("Connecting to database...")
    clients.database = Database(
        url=db_dsn(
            scheme=settings.DB_SCHEME,
            user=settings.DB_USER,
            passwd=settings.DB_PASS,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
        )
    )
    await clients.database.connect()
    logger.info("Connected to database.")


@app.on_event("shutdown")
async def shutdown_database():
    logger.info("Closing database connection...")
    await clients.database.disconnect()
    del clients.database
    logger.info("Closed database connection.")


def redis_dsn(
    scheme: str,
    host: str,
    port: int,
    passwd: str,
    database: int,
) -> str:
    # TODO: *optional* passwd support?
    # TODO: optional user support?
    return f"{scheme}://{passwd}@{host}:{port}/{database}?password={passwd}"


@app.on_event("startup")
async def start_redis():
    logger.info("Connecting to Redis...")
    clients.redis = await redis.asyncio.from_url(
        url=redis_dsn(
            scheme=settings.REDIS_SCHEME,
            passwd=settings.REDIS_PASS,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            database=settings.REDIS_DB,
        ),
    )
    logger.info("Connected to Redis.")


@app.on_event("shutdown")
async def shutdown_redis():
    logger.info("Closing Redis connection...")
    await clients.redis.close()
    del clients.redis
    logger.info("Closed Redis connection.")


def parse_login_data(data: bytes) -> dict[str, Any]:
    """Parse data from the body of a login request."""
    (
        username,
        password_md5,
        remainder,
    ) = data.decode().split("\n", maxsplit=2)

    (
        osu_version,
        utc_offset,
        display_city,
        client_hashes,
        pm_private,
    ) = remainder.split("|", maxsplit=4)

    (
        osu_path_md5,
        adapters_str,
        adapters_md5,
        uninstall_md5,
        disk_signature_md5,
    ) = client_hashes[:-1].split(":", maxsplit=4)

    return {
        "username": username,
        "password_md5": password_md5,
        "osu_version": osu_version,
        "utc_offset": int(utc_offset),
        "display_city": display_city == "1",
        "pm_private": pm_private == "1",
        "osu_path_md5": osu_path_md5,
        "adapters_str": adapters_str,
        "adapters_md5": adapters_md5,
        "uninstall_md5": uninstall_md5,
        "disk_signature_md5": disk_signature_md5,
    }


def get_global_rank(account_id: int) -> int:
    """Get the global rank of an account."""
    return 1


def get_country_rank(account_id: int) -> int:
    """Get the country rank of an account."""
    return 1


@app.post("/")
async def handle_bancho_request(request: Request):
    if "osu-token" not in request.headers:
        login_data = parse_login_data(await request.body())

        account = await accounts.fetch_by_username(login_data["username"])
        if not account:
            return Response(
                content=(
                    packets.write_user_id_packet(user_id=-1)
                    + packets.write_notification_packet(
                        "Incorrect username."  # "Incorrect username or password."
                    )
                ),
                headers={"cho-token": "no"},
            )

        if not security.check_password(
            password=login_data["password_md5"],
            hashword=account["password"].encode(),
        ):
            return Response(
                content=(
                    packets.write_user_id_packet(user_id=-1)
                    + packets.write_notification_packet(
                        "Incorrect password."  # "Incorrect username or password."
                    )
                ),
                headers={"cho-token": "no"},
            )

        session = await sessions.create(
            session_id=uuid4(),
            account_id=account["account_id"],
        )

        response_data = bytearray()

        # we need to send a few things to the client for it to be considered a "complete" login
        # [done] their session id (token)

        # protocol version
        response_data += packets.write_protocol_version_packet(19)

        # user id
        response_data += packets.write_user_id_packet(account["account_id"])

        # privileges
        response_data += packets.write_user_privileges_packet(
            privileges.server_to_client_privileges(account["privileges"])
        )

        # channels (and channel info end)
        for channel in await channels.fetch_all():
            response_data += packets.write_channel_info_packet(
                channel["name"],
                channel["topic"],
                channel["num_sessions"],
            )

        response_data += packets.write_channel_info_end_packet()

        # own presence

        own_presence = await presences.create(
            account_id=account["account_id"],
            username=account["username"],
            utc_offset=login_data["utc_offset"],
            country=account["country"],
            bancho_privileges=privileges.server_to_client_privileges(
                account["privileges"]
            ),
            game_mode=0,
            latitude=0.0,  # TODO
            longitude=0.0,  # TODO
            action=0,
            info_text="",
            beatmap_md5="",
            beatmap_id=0,
            mods=0,
            mode=0,
        )

        # own stats
        own_stats = await stats.fetch_one(
            account_id=account["account_id"],
            game_mode=own_presence["game_mode"],
        )
        if not own_stats:
            return Response(
                content=(
                    packets.write_user_id_packet(user_id=-1)
                    + packets.write_notification_packet("Own stats not found.")
                ),
                headers={"cho-token": "no"},
            )

        response_data += packets.write_user_presence_packet(
            own_presence["account_id"],
            own_presence["username"],
            own_presence["utc_offset"],
            geolocation.country_str_to_int(own_presence["country"]),
            # TODO: is this right?
            privileges.server_to_client_privileges(own_presence["bancho_privileges"]),
            own_presence["game_mode"],
            own_presence["latitude"],
            own_presence["longitude"],
            get_global_rank(own_presence["account_id"]),
        )

        response_data += packets.write_user_stats_packet(
            own_stats["account_id"],
            own_presence["action"],
            own_presence["info_text"],
            own_presence["beatmap_md5"],
            own_presence["beatmap_id"],
            own_presence["mods"],
            own_presence["mode"],
            own_stats["ranked_score"],
            own_stats["accuracy"],
            own_stats["play_count"],
            own_stats["total_score"],
            get_global_rank(own_stats["account_id"]),
            own_stats["performance_points"],
        )

        for other_session in await sessions.fetch_all():
            # presence of all other players (& bots)
            others_presence = await presences.fetch_one(
                account_id=other_session["account_id"]
            )
            if not others_presence:
                return Response(
                    content=(
                        packets.write_user_id_packet(user_id=-1)
                        + packets.write_notification_packet(
                            "Other's presence not found."
                        )
                    ),
                    headers={"cho-token": "no"},
                )

            # stats of all other players (& bots)
            others_stats = await stats.fetch_one(
                account_id=other_session["account_id"],
                game_mode=others_presence["game_mode"],
            )
            if not others_stats:
                return Response(
                    content=(
                        packets.write_user_id_packet(user_id=-1)
                        + packets.write_notification_packet("Other's stats not found.")
                    ),
                    headers={"cho-token": "no"},
                )

            response_data += packets.write_user_presence_packet(
                others_presence["account_id"],
                others_presence["username"],
                others_presence["utc_offset"],
                geolocation.country_str_to_int(others_presence["country"]),
                # TODO: is this right?
                privileges.server_to_client_privileges(
                    others_presence["bancho_privileges"]
                ),
                others_presence["game_mode"],
                others_presence["latitude"],
                others_presence["longitude"],
                get_global_rank(others_stats["account_id"]),
            )

            response_data += packets.write_user_stats_packet(
                others_stats["account_id"],
                others_presence["action"],
                others_presence["info_text"],
                others_presence["beatmap_md5"],
                others_presence["beatmap_id"],
                others_presence["mods"],
                others_presence["mode"],
                others_stats["ranked_score"],
                others_stats["accuracy"],
                others_stats["play_count"],
                others_stats["total_score"],
                get_global_rank(others_stats["account_id"]),
                others_stats["performance_points"],
            )

        response_data += packets.write_notification_packet(
            "Welcome to the osu!bancho server!"
        )

        # next, we can add these additional "features"
        # silence end
        # whether they're restricted
        # friend list
        # main menu icon
        print("success")
        return Response(
            content=bytes(response_data),
            headers={"cho-token": str(session["session_id"])},
        )
    else:
        # TODO: handle an authenticated request
        ...


# POST c.ppy.sh/
# @router.post("/")
# def handle_bancho_request_old(request):
#     if "osu-token" not in request.headers:
#         # this is a login request
#         login_data = read_login_body(request.body)

#         account = fetch_account_by_name(login_data["username"])
#         if not account:
#             return

#         if login_data["password"] != account["password"]:
#             return

#         session = create_session(login_data)

#         return Response(
#             content=format_response(session),
#             headers={"osu-token": request.headers["osu-token"]},
#         )
#     else:
#         # this is an authenticated request
#         session = fetch_session_by_token(request.headers["osu-token"])
#         if not session:
#             return

#         response_packets = []

#         # read bancho packets from the request body
#         packets = read_packets(request.body)
#         for packet in packets:
#             response_packet = handle_packet(session, packet)
#             response_packets.append(response_packet)

#         return Response(content=format_response(response_packets))
