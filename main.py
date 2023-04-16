#!/usr/bin/env python3
from typing import Any
from uuid import uuid4

import redis.asyncio
from databases import Database
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response

import clients
import packets
import settings
from repositories import accounts
from repositories import channels
from repositories import sessions

app = FastAPI()
router = APIRouter()

app.include_router(router)


def dsn(
    scheme: str,
    user: str,
    passwd: str,
    host: str,
    port: int,
    database: str | int,
) -> str:
    return f"{scheme}://{user}:{passwd}@{host}:{port}/{database}"


@app.on_event("startup")
async def start_database():
    clients.database = Database(
        url=dsn(
            scheme=settings.DB_SCHEME,
            user=settings.DB_USER,
            passwd=settings.DB_PASS,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
        )
    )


@app.on_event("shutdown")
async def shutdown_database():
    await clients.database.disconnect()


@app.on_event("startup")
async def start_redis():
    clients.redis = await redis.asyncio.from_url(
        url=dsn(
            scheme=settings.REDIS_SCHEME,
            user=settings.REDIS_USER,
            passwd=settings.REDIS_PASS,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            database=settings.REDIS_DB,
        ),
    )


@app.on_event("shutdown")
async def shutdown_redis():
    await clients.redis.close()


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
        "password_md5": password_md5.encode(),
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


@app.post("/")
async def handle_bancho_request(request: Request):
    if "osu-token" not in request.headers:
        login_data = parse_login_data(await request.body())

        account = await accounts.fetch_by_username(login_data["username"])
        if not account:
            return Response(packets.write_user_id_packet(user_id=-1))

        if login_data["password"] != account["password"]:
            return Response(packets.write_user_id_packet(user_id=-1))

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
        response_data += packets.write_user_privileges_packet(account["privileges"])

        # channels (and channel info end)
        for channel in await channels.fetch_all():
            response_data += packets.write_channel_info_packet(
                channel["name"],
                channel["topic"],
                channel["num_sessions"],
            )

        response_data += packets.write_channel_info_end_packet()

        # own presence
        own_presence = await presences.fetch_one(account_id=account["account_id"])
        if not own_presence:
            return Response(packets.write_user_id_packet(user_id=-1))

        response_data += packets.write_user_presence_packet(
            own_presence["account_id"],
            own_presence["username"],
            own_presence["utc_offset"],
            own_presence["country_code"],
            own_presence["bancho_privileges"],
            own_presence["game_mode"],
            own_presence["latitude"],
            own_presence["longitude"],
            own_presence["global_rank"],
        )

        # own stats
        own_stats = await stats.fetch_one(account_id=account["account_id"])
        if not own_stats:
            return Response(packets.write_user_id_packet(user_id=-1))

        response_data += packets.write_user_stats_packet(
            own_stats["account_id"],
            own_stats["action"],
            own_stats["info_text"],
            own_stats["beatmap_md5"],
            own_stats["mods"],
            own_stats["mode"],
            own_stats["beatmap_id"],
            own_stats["ranked_score"],
            own_stats["accuracy"],
            own_stats["playcount"],
            own_stats["total_score"],
            own_stats["global_rank"],
            own_stats["pp"],
        )

        for other_session in await sessions.fetch_all():
            # presence of all other players (& bots)
            others_presence = await presences.fetch_one(
                account_id=other_session["account_id"]
            )
            if not others_presence:
                return Response(packets.write_user_id_packet(user_id=-1))

            response_data += packets.write_user_presence_packet(
                others_presence["account_id"],
                others_presence["username"],
                others_presence["utc_offset"],
                others_presence["country_code"],
                others_presence["bancho_privileges"],
                others_presence["game_mode"],
                others_presence["latitude"],
                others_presence["longitude"],
                others_presence["global_rank"],
            )

            # stats of all other players (& bots)
            others_stats = await stats.fetch_one(account_id=other_session["account_id"])
            if not others_stats:
                return Response(packets.write_user_id_packet(user_id=-1))

            response_data += packets.write_user_stats_packet(
                others_stats["account_id"],
                others_stats["action"],
                others_stats["info_text"],
                others_stats["beatmap_md5"],
                others_stats["mods"],
                others_stats["mode"],
                others_stats["beatmap_id"],
                others_stats["ranked_score"],
                others_stats["accuracy"],
                others_stats["playcount"],
                others_stats["total_score"],
                others_stats["global_rank"],
                others_stats["pp"],
            )

        # next, we can add these additional "features"
        # silence end
        # whether they're restricted
        # friend list
        # main menu icon

        return Response(
            content=bytes(response_data),
            headers={"cho-token": session["session_id"]},
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
