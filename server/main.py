#!/usr/bin/env python3
import ipaddress
from datetime import datetime
from typing import Any
from uuid import UUID
from uuid import uuid4

import aiosu
import redis.asyncio
from aiobotocore.session import get_session
from databases import Database
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Query
from fastapi import Request
from fastapi import Response

from server import clients
from server import geolocation
from server import logger
from server import packet_handlers
from server import packets
from server import privileges
from server import ranking
from server import security
from server import settings
from server.adapters import ip_api
from server.adapters import osu_api_v2
from server.repositories import accounts
from server.repositories import beatmaps
from server.repositories import channel_members
from server.repositories import channels
from server.repositories import packet_bundles
from server.repositories import scores
from server.repositories import sessions
from server.repositories import stats
from server.repositories.accounts import Account
from server.repositories.beatmaps import Beatmap
from server.repositories.scores import Score

app = FastAPI()

osu_web_handler = APIRouter()
bancho_router = APIRouter()

app.host("osu.cmyui.xyz", osu_web_handler)

for subdomain in ("c", "ce", "c4", "c5", "c6"):
    app.host(f"{subdomain}.cmyui.xyz", bancho_router)


logger.configure_logging(
    app_env=settings.APP_ENV,
    log_level=settings.APP_LOG_LEVEL,
)


@bancho_router.get("/")
async def bancho_home_page():
    return "Hello, bancho!"


@osu_web_handler.get("/")
async def osu_web_home_page():
    return "Hello, osu!web!"


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


@app.on_event("startup")
async def start_osu_api_client():
    clients.osu_api = aiosu.v2.Client(
        client_id=settings.OSU_API_V2_CLIENT_ID,
        client_secret=settings.OSU_API_V2_CLIENT_SECRET,
        token=aiosu.models.OAuthToken(),
    )


@app.on_event("shutdown")
async def shutdown_osu_api_client():
    await clients.osu_api.close()
    del clients.osu_api


@app.on_event("startup")
async def start_s3_client():
    session = get_session()
    clients.s3_client = await session._create_client(  # type: ignore
        service_name="s3",
        region_name=settings.S3_BUCKET_REGION,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        endpoint_url=settings.S3_ENDPOINT_URL,
    )
    await clients.s3_client.__aenter__()


@app.on_event("shutdown")
async def shutdown_s3_client():
    await clients.s3_client.__aexit__(None, None, None)
    del clients.s3_client


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


async def handle_login(request: Request) -> Response:
    login_data = parse_login_data(await request.body())

    account = await accounts.fetch_by_username(login_data["username"])
    if not account:
        return Response(
            content=(
                packets.write_user_id_packet(-1)
                + packets.write_notification_packet("Incorrect username or password.")
            ),
            headers={"cho-token": "no"},
        )

    if not security.check_password(
        password=login_data["password_md5"],
        hashword=account["password"].encode(),
    ):
        return Response(
            content=(
                packets.write_user_id_packet(-1)
                + packets.write_notification_packet("Incorrect username or password.")
            ),
            headers={"cho-token": "no"},
        )

    # TODO: support for this specifically for tournament clients
    other_session = await sessions.fetch_by_username(login_data["username"])
    if other_session is not None:
        # TODO: store the last time a client pinged the server, and check that instead
        time_since_last_update = datetime.now() - other_session["updated_at"]

        if time_since_last_update.total_seconds() > 10:  # trust the new user
            await sessions.delete_by_id(other_session["session_id"])
        else:
            return Response(
                content=(
                    packets.write_user_id_packet(-1)
                    + packets.write_notification_packet("User already logged in.")
                ),
                headers={"cho-token": "no"},
            )

    raw_ip_address = request.headers.get("X-Real-IP")
    if raw_ip_address is None:
        return Response(
            content=(
                packets.write_user_id_packet(-1)
                + packets.write_notification_packet(
                    "Could not determine your IP address."
                )
            ),
            headers={"cho-token": "no"},
        )

    ip_address = ipaddress.ip_address(raw_ip_address)

    if ip_address.is_private:
        # TODO: something better than this, perhaps?
        user_geolocation = {"latitude": 0.0, "longitude": 0.0}
    else:
        user_geolocation = await ip_api.fetch_geolocation_from_ip_address(
            raw_ip_address
        )
        if user_geolocation is None:
            return Response(
                content=(
                    packets.write_user_id_packet(-1)
                    + packets.write_notification_packet(
                        "Could not determine your geolocation."
                    )
                ),
                headers={"cho-token": "no"},
            )

    own_session = await sessions.create(
        session_id=uuid4(),
        account_id=account["account_id"],
        presence={
            "account_id": account["account_id"],
            "username": account["username"],
            "utc_offset": login_data["utc_offset"],
            "country": account["country"],
            "bancho_privileges": privileges.server_to_client_privileges(
                account["privileges"]
            ),
            "game_mode": 0,
            "latitude": user_geolocation["latitude"],
            "longitude": user_geolocation["longitude"],
            "action": 0,
            "info_text": "",
            "beatmap_md5": "",
            "beatmap_id": 0,
            "mods": 0,
            "mode": 0,
            "spectator_host_session_id": None,
        },
    )
    assert own_session["presence"] is not None  # TODO: is there a better way?

    # we will respond to this request with several bancho packets
    response_data = bytearray()

    # protocol version
    response_data += packets.write_protocol_version_packet(19)

    # user id
    response_data += packets.write_user_id_packet(account["account_id"])

    # user privileges
    response_data += packets.write_user_privileges_packet(
        privileges.server_to_client_privileges(account["privileges"])
    )

    # osu chat channels
    for channel in await channels.fetch_all():
        # TODO: privilege check - do they have access to this channel?
        current_channel_members = await channel_members.members(channel["channel_id"])

        response_data += packets.write_channel_info_packet(
            channel["name"],
            channel["topic"],
            len(current_channel_members),
        )

    # notify the client that we're done sending channel info
    response_data += packets.write_channel_info_end_packet()

    # user presence
    own_presence_packet_data = packets.write_user_presence_packet(
        own_session["presence"]["account_id"],
        own_session["presence"]["username"],
        own_session["presence"]["utc_offset"],
        geolocation.country_str_to_int(own_session["presence"]["country"]),
        # TODO: is this right?
        privileges.server_to_client_privileges(
            own_session["presence"]["bancho_privileges"]
        ),
        own_session["presence"]["game_mode"],
        int(own_session["presence"]["latitude"]),
        int(own_session["presence"]["longitude"]),
        ranking.get_global_rank(own_session["presence"]["account_id"]),
    )

    # user stats
    own_stats = await stats.fetch_one(
        account_id=account["account_id"],
        game_mode=own_session["presence"]["game_mode"],
    )
    if not own_stats:
        return Response(
            content=(
                packets.write_user_id_packet(-1)
                + packets.write_notification_packet("Own stats not found.")
            ),
            headers={"cho-token": "no"},
        )

    own_stats_packet_data = packets.write_user_stats_packet(
        own_stats["account_id"],
        own_session["presence"]["action"],
        own_session["presence"]["info_text"],
        own_session["presence"]["beatmap_md5"],
        own_session["presence"]["mods"],
        own_session["presence"]["mode"],
        own_session["presence"]["beatmap_id"],
        own_stats["ranked_score"],
        own_stats["accuracy"],
        own_stats["play_count"],
        own_stats["total_score"],
        ranking.get_global_rank(own_stats["account_id"]),
        own_stats["performance_points"],
    )

    # send our presence & stats to ourselves
    response_data += own_presence_packet_data
    response_data += own_stats_packet_data

    for other_session in await sessions.fetch_all(osu_clients_only=True):
        if other_session["session_id"] == own_session["session_id"]:
            continue

        assert other_session["presence"] is not None  # TODO: is there a better way?

        # send other user's presence to us
        response_data += packets.write_user_presence_packet(
            other_session["presence"]["account_id"],
            other_session["presence"]["username"],
            other_session["presence"]["utc_offset"],
            geolocation.country_str_to_int(other_session["presence"]["country"]),
            # TODO: is this right?
            privileges.server_to_client_privileges(
                other_session["presence"]["bancho_privileges"]
            ),
            other_session["presence"]["game_mode"],
            int(other_session["presence"]["latitude"]),
            int(other_session["presence"]["longitude"]),
            ranking.get_global_rank(other_session["account_id"]),
        )

        # send other user's stats to us
        others_stats = await stats.fetch_one(
            account_id=other_session["account_id"],
            game_mode=other_session["presence"]["game_mode"],
        )
        if not others_stats:
            return Response(
                content=(
                    packets.write_user_id_packet(-1)
                    + packets.write_notification_packet("Other's stats not found.")
                ),
                headers={"cho-token": "no"},
            )

        response_data += packets.write_user_stats_packet(
            others_stats["account_id"],
            other_session["presence"]["action"],
            other_session["presence"]["info_text"],
            other_session["presence"]["beatmap_md5"],
            other_session["presence"]["mods"],
            other_session["presence"]["mode"],
            other_session["presence"]["beatmap_id"],
            others_stats["ranked_score"],
            others_stats["accuracy"],
            others_stats["play_count"],
            others_stats["total_score"],
            ranking.get_global_rank(others_stats["account_id"]),
            others_stats["performance_points"],
        )

        # send our presence & stats to other user
        await packet_bundles.enqueue(
            other_session["session_id"],
            data=own_presence_packet_data + own_stats_packet_data,
        )

    # welcome message/notification
    response_data += packets.write_notification_packet(
        "Welcome to the osu!bancho server!"
    )

    # TODO: silence end

    # TODO: whether they're restricted

    # TODO: friends list

    # TODO: main menu icon

    logger.info(
        "User login successful",
        account_id=own_session["account_id"],
        session_id=own_session["session_id"],
    )

    return Response(
        content=bytes(response_data),
        headers={"cho-token": str(own_session["session_id"])},
    )


async def handle_bancho_request(request: Request) -> Response:
    # authenticate the request
    session_id = UUID(request.headers["osu-token"])
    session = await sessions.fetch_by_id(session_id)
    if session is None:
        return Response(
            content=(
                packets.write_restart_packet(millseconds_until_restart=0)
                + packets.write_notification_packet("The server has restarted.")
            )
        )

    # read packets
    request_body = await request.body()
    osu_packets = packets.read_packets(request_body)

    # handle packets
    for packet in osu_packets:
        packet_handler = packet_handlers.get_packet_handler(packet.packet_id)
        if packet_handler is None:
            logger.warning("Unhandled packet type", packet_id=packet.packet_id)
            continue

        await packet_handler(session, packet.packet_data)
        logger.info("Handled packet", packet_id=packet.packet_id)

    # dequeue all packets to send back to the client
    response_content = bytearray()
    own_packet_bundles = await packet_bundles.dequeue_all(session["session_id"])
    for packet_bundle in own_packet_bundles:
        response_content.extend(packet_bundle["data"])

    return Response(
        content=bytes(response_content),
        headers={"cho-token": str(session["session_id"])},
    )


@bancho_router.post("/")
async def handle_bancho_http_request(request: Request):
    if "osu-token" not in request.headers:
        response = await handle_login(request)
    else:  # they don't have a token
        response = await handle_bancho_request(request)

    return response


def create_beatmap_filename(
    artist: str,
    title: str,
    version: str,
    creator: str,
) -> str:
    return f"{artist} - {title} ({creator}) [{version}].osu"


# GET /web/osu-osz2-getscores.php
# ?s=0
# &vv=4
# &v=1
# &c=1cf5b2c2edfafd055536d2cefcb89c0e
# &f=FAIRY+FORE+-+Vivid+(Hitoshirenu+Shourai)+%5bInsane%5d.osu
# &m=0
# &i=141
# &mods=192
# &h=
# &a=0
# &us=cmyui
# &ha=0cc175b9c0f1b6a831c399e269772661
@osu_web_handler.get("/web/osu-osz2-getscores.php")
async def get_scores_handler(
    username: str = Query(..., alias="us"),
    password_md5: str = Query(..., alias="ha"),
    requesting_score_data: bool = Query(..., alias="s"),
    leaderboard_version: int = Query(..., alias="vv"),
    leaderboard_type: int = Query(..., alias="v"),
    beatmap_md5: str = Query(..., alias="c"),
    beatmap_filename: str = Query(..., alias="f"),
    game_mode: int = Query(..., alias="m"),
    beatmap_set_id: int = Query(..., alias="i"),
    mods: int = Query(..., alias="mods"),
    map_package_hash: str = Query(..., alias="h"),
    aqn_files_found: bool = Query(..., alias="a"),
):
    # TODO: fix the responses in the case of an error
    account = await accounts.fetch_by_username(username)
    if account is None:
        return

    session = await sessions.fetch_by_username(username)
    if session is None:
        return

    if not security.check_password(
        password=password_md5,
        hashword=account["password"].encode(),
    ):
        return

    beatmap = await beatmaps.fetch_one_by_md5(beatmap_md5)
    if beatmap is None:
        # attempt to fetch the beatmap from the osu! api JIT
        api_v2_beatmap = await osu_api_v2.lookup_beatmap(beatmap_md5=beatmap_md5)
        if api_v2_beatmap is None:
            logger.error("Beatmap not found", beatmap_md5=beatmap_md5)
            return

        assert api_v2_beatmap.beatmap_md5 is not None
        assert api_v2_beatmap.beatmapset is not None
        assert api_v2_beatmap.last_updated is not None

        beatmap = await beatmaps.create(
            api_v2_beatmap.beatmap_id,
            api_v2_beatmap.beatmap_set_id,
            api_v2_beatmap.ranked_status,
            api_v2_beatmap.beatmap_md5,
            api_v2_beatmap.beatmapset.artist,
            api_v2_beatmap.beatmapset.title,
            api_v2_beatmap.version,
            api_v2_beatmap.beatmapset.creator_name,
            create_beatmap_filename(
                artist=api_v2_beatmap.beatmapset.artist,
                title=api_v2_beatmap.beatmapset.title,
                version=api_v2_beatmap.version,
                creator=api_v2_beatmap.beatmapset.creator_name,
            ),
            api_v2_beatmap.last_updated,
            api_v2_beatmap.total_length,
            api_v2_beatmap.max_combo or 0,
            False,  # manually ranked
            0,  # plays
            0,  # passes
            api_v2_beatmap.game_mode,
            api_v2_beatmap.bpm or 0,
            api_v2_beatmap.cs or 0,
            api_v2_beatmap.ar or 0,
            api_v2_beatmap.od or 0,
            api_v2_beatmap.hp or 0,
            api_v2_beatmap.star_rating,
        )

    # TODO: leaderboard type handling

    leaderboard_scores = await scores.fetch_many(
        beatmap_md5=beatmap_md5,
        submission_status=2,  # TODO?
        game_mode=game_mode,
        sort_by="performance_points",  # TODO: score for certain gamemodes?
        page_size=50,
    )

    personal_best_scores = await scores.fetch_many(
        account_id=account["account_id"],
        beatmap_md5=beatmap_md5,
        submission_status=2,  # TODO?
        game_mode=game_mode,
        sort_by="performance_points",  # TODO: score for certain gamemodes?
        page_size=1,
    )
    if personal_best_scores:
        personal_best_score = personal_best_scores[0]
    else:
        personal_best_score = None

    return format_leaderboard_response(
        leaderboard_scores,
        personal_best_score,
        account,
        beatmap,
    )


def format_leaderboard_response(
    leaderboard_scores: list[Score],
    personal_best_score: Score | None,
    account: Account,
    beatmap: Beatmap,
) -> str:
    """\
    {ranked_status}|{serv_has_osz2}|{bid}|{bsid}|{len(scores)}|{fa_track_id}|{fa_license_text}
    {offset}\n{beatmap_name}\n{rating}
    {id}|{name}|{score}|{max_combo}|{n50}|{n100}|{n300}|{nmiss}|{nkatu}|{ngeki}|{perfect}|{mods}|{userid}|{rank}|{time}|{has_replay}
    {id}|{name}|{score}|{max_combo}|{n50}|{n100}|{n300}|{nmiss}|{nkatu}|{ngeki}|{perfect}|{mods}|{userid}|{rank}|{time}|{has_replay}
    ...
    """
    # 3rd line is peronsal best, rest are leaderboard scores

    buffer = ""

    # first line
    buffer += f"{beatmap['ranked_status']}|0|{beatmap['beatmap_id']}|{beatmap['beatmap_set_id']}|{len(leaderboard_scores)}|0|0\n"

    # second line
    beatmap_name = "{artist} - {title} [{version}]".format(**beatmap)
    buffer += f"0\n{beatmap_name}\n{beatmap['star_rating']}\n"

    # third line
    if personal_best_score is None:
        buffer += "0\n"
    else:
        buffer += (
            f"{personal_best_score['score_id']}|"
            f"{account['username']}|"
            f"{personal_best_score['score']}|"
            f"{personal_best_score['highest_combo']}|"
            f"{personal_best_score['num_50s']}|"
            f"{personal_best_score['num_100s']}|"
            f"{personal_best_score['num_300s']}|"
            f"{personal_best_score['num_misses']}|"
            f"{personal_best_score['num_katus']}|"
            f"{personal_best_score['num_gekis']}|"
            f"{personal_best_score['full_combo']}|"
            f"{personal_best_score['mods']}|"
            f"{account['account_id']}|"
            f"{personal_best_score['rank']}|"
            f"{personal_best_score['time']}|"
            f"{personal_best_score['has_replay']}\n"
        )

    # rest of the lines
    for score in leaderboard_scores:
        buffer += (
            f"{score['score_id']}|"
            f"{score['username']}|"
            f"{score['score']}|"
            f"{score['highest_combo']}|"
            f"{score['num_50s']}|"
            f"{score['num_100s']}|"
            f"{score['num_300s']}|"
            f"{score['num_misses']}|"
            f"{score['num_katus']}|"
            f"{score['num_gekis']}|"
            f"{score['full_combo']}|"
            f"{score['mods']}|"
            f"{score['account_id']}|"
            f"{score['rank']}|"
            f"{score['time']}|"
            f"{score['has_replay']}\n"
        )

    return buffer
