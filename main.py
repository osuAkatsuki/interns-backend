#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi import Response, Request
from repositories import sessions
from uuid import uuid4
from databases import Database
import uvicorn
from repositories import accounts, channels
import settings
from fastapi import APIRouter

import clients

app = FastAPI()
router = APIRouter()


def dsn(
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


from typing import Any
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

def login_failed_data() -> bytes:
    return b"\x05\x00\x00\x04\x00\x00\x00\xff\xff\xff\xff"
    return bytes([5, 0, 0, 4, 0, 0, 0, 255, 255, 255, 255])

@app.post("/")
async def handle_bancho_request(request: Request):
    if "osu-token" not in request.headers:
        login_data = parse_login_data(await request.body())

        account = await accounts.fetch_by_username(login_data["username"])
        if not account:
            return Response(content=login_failed_data())

        if login_data['password'] != account['password']:
            return Response(content=login_failed_data())

        session = await sessions.create(
            session_id=uuid4(),
            account_id=account['account_id'],
        )

        # we need to fetch a few things for login to be "complete" on the client

        # 1. channels
        osu_channels = await channels.fetch_all()


        # 2.
        #
        # we need to encode this data using the bancho protocol
        # into individual packets to send back to the client
        #
        ...


        return Response(content=b"hello")


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
