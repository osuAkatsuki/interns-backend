#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi import Response, Request
from repositories import sessions
from uuid import uuid4
from typing import Any
import redis.asyncio
from databases import Database
import uvicorn
from repositories import accounts, channels
import settings
from fastapi import APIRouter

import packets
import clients

app = FastAPI()
router = APIRouter()


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
            response_data += packets.write_channel_info_packet(channel)

        response_data += packets.write_channel_info_end_packet()

        # own presence
        presence = await presences.fetch_one(account_id=account["account_id"])
        if not presence:
            return Response(packets.write_user_id_packet(user_id=-1))

        response_data += packets.write_user_presence(presence)

        # own stats
        stats = await stats.fetch_one(account_id=account["account_id"])
        if not stats:
            return Response(packets.write_user_id_packet(user_id=-1))
        response_data += packets.write_user_stats(stats)

        for other_session in sessions.fetch_all():
            # presence of all other players (& bots)
            presence = await presences.fetch_one(account_id=other_session["account_id"])
            if not presence:
                return Response(packets.write_user_id_packet(user_id=-1))

            response_data += packets.write_user_presence(presence)

            # stats of all other players (& bots)
            stats = await stats.fetch_one(account_id=other_session["account_id"])
            if not stats:
                return Response(packets.write_user_id_packet(user_id=-1))

            response_data += packets.write_user_stats(stats)

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


if __name__ == "__main__":
    uvicorn.run(app)
