import ipaddress
from datetime import datetime
from typing import TypedDict
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Request
from fastapi import Response

from app import geolocation
from app import logger
from app import packet_handlers
from app import packets
from app import privileges
from app import ranking
from app import security
from app.adapters import ip_api
from app.game_modes import GameMode
from app.mods import Mods
from app.privileges import ServerPrivileges
from app.repositories import accounts
from app.repositories import channel_members
from app.repositories import channels
from app.repositories import osu_sessions
from app.repositories import packet_bundles
from app.repositories import relationships
from app.repositories import stats

bancho_router = APIRouter(default_response_class=Response)


@bancho_router.get("/")
async def bancho_home_page():
    return "Hello, bancho!"


class LoginData(TypedDict):
    username: str
    password_md5: str
    osu_version: str
    utc_offset: int
    display_city: bool
    pm_private: bool
    osu_path_md5: str
    adapters_str: str
    adapters_md5: str
    uninstall_md5: str
    disk_signature_md5: str


def parse_login_data(data: bytes) -> LoginData:
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

    other_osu_session = await osu_sessions.fetch_primary_by_username(
        login_data["username"]
    )

    vanilla_game_mode = GameMode.VN_OSU

    own_osu_session = await osu_sessions.create(
        osu_session_id=uuid4(),
        account_id=account["account_id"],
        username=account["username"],
        utc_offset=login_data["utc_offset"],
        country=account["country"],
        privileges=account["privileges"],
        game_mode=vanilla_game_mode,
        latitude=user_geolocation["latitude"],
        longitude=user_geolocation["longitude"],
        action=0,
        info_text="",
        beatmap_md5="",
        beatmap_id=0,
        mods=Mods.NOMOD,
        pm_private=login_data["pm_private"],
        receive_match_updates=False,
        spectator_host_osu_session_id=None,
        away_message=None,
        multiplayer_match_id=None,
        last_communicated_at=datetime.now(),
        last_np_beatmap_id=None,
        primary=(
            # this is either our first session or we're logging in from a tournament spectator client
            # TODO: limit the number of spectators clients which can connect simultaneously?
            other_osu_session is None
            or login_data["osu_version"].endswith("tourney")
        ),
    )

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
    for channel in await channels.fetch_many():
        if channel["temporary"]:
            continue

        if (account["privileges"] & channel["read_privileges"]) == 0:
            continue

        if channel == "#lobby":
            continue

        # TODO: handle send all presence status?

        current_channel_members = await channel_members.members(channel["channel_id"])

        response_data += packets.write_channel_info_packet(
            channel["name"],
            channel["topic"],
            len(current_channel_members),
        )

    # notify the client that we're done sending channel info
    response_data += packets.write_channel_listing_complete_packet()

    own_global_rank = await ranking.get_global_rank(
        own_osu_session["account_id"],
        own_osu_session["game_mode"],
    )

    # user presence
    own_presence_packet_data = packets.write_user_presence_packet(
        own_osu_session["account_id"],
        own_osu_session["username"],
        own_osu_session["utc_offset"],
        geolocation.country_str_to_int(own_osu_session["country"]),
        privileges.server_to_client_privileges(own_osu_session["privileges"]),
        vanilla_game_mode,
        int(own_osu_session["latitude"]),
        int(own_osu_session["longitude"]),
        own_global_rank,
    )

    own_stats = await stats.fetch_one(
        account_id=account["account_id"],
        game_mode=own_osu_session["game_mode"],
    )
    if not own_stats:
        return Response(
            content=(
                packets.write_user_id_packet(-1)
                + packets.write_notification_packet("Own stats not found.")
            ),
            headers={"cho-token": "no"},
        )

    own_global_rank = await ranking.get_global_rank(
        own_stats["account_id"],
        own_stats["game_mode"],
    )

    own_stats_packet_data = packets.write_user_stats_packet(
        own_stats["account_id"],
        own_osu_session["action"],
        own_osu_session["info_text"],
        own_osu_session["beatmap_md5"],
        own_osu_session["mods"],
        vanilla_game_mode,
        own_osu_session["beatmap_id"],
        own_stats["ranked_score"],
        own_stats["accuracy"],
        own_stats["play_count"],
        own_stats["total_score"],
        own_global_rank,
        own_stats["performance_points"],
    )

    # send our presence & stats to ourselves
    response_data += own_presence_packet_data
    response_data += own_stats_packet_data

    for other_osu_session in await osu_sessions.fetch_all():
        if other_osu_session["osu_session_id"] == own_osu_session["osu_session_id"]:
            continue

        other_global_rank = await ranking.get_global_rank(
            other_osu_session["account_id"],
            own_osu_session["game_mode"],
        )

        # send other user's presence to us
        response_data += packets.write_user_presence_packet(
            other_osu_session["account_id"],
            other_osu_session["username"],
            other_osu_session["utc_offset"],
            geolocation.country_str_to_int(other_osu_session["country"]),
            privileges.server_to_client_privileges(other_osu_session["privileges"]),
            vanilla_game_mode,
            int(other_osu_session["latitude"]),
            int(other_osu_session["longitude"]),
            other_global_rank,
        )

        # send other user's stats to us
        others_stats = await stats.fetch_one(
            account_id=other_osu_session["account_id"],
            game_mode=other_osu_session["game_mode"],
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
            other_osu_session["action"],
            other_osu_session["info_text"],
            other_osu_session["beatmap_md5"],
            other_osu_session["mods"],
            vanilla_game_mode,
            other_osu_session["beatmap_id"],
            others_stats["ranked_score"],
            others_stats["accuracy"],
            others_stats["play_count"],
            others_stats["total_score"],
            other_global_rank,
            others_stats["performance_points"],
        )

        if account["privileges"] & ServerPrivileges.UNRESTRICTED:
            # send our presence & stats to other user
            await packet_bundles.enqueue(
                other_osu_session["osu_session_id"],
                data=own_presence_packet_data + own_stats_packet_data,
            )

    # welcome message/notification
    response_data += packets.write_notification_packet(
        "Welcome to the osu!bancho server!"
    )

    if account["silence_end"] is not None:
        seconds_remaining = (datetime.now() - account["silence_end"]).total_seconds()

        if seconds_remaining > 0:
            response_data += packets.write_silence_end_packet(
                seconds_remaining=int(seconds_remaining),
            )
        else:
            await accounts.partial_update(account["account_id"], silence_end=None)

    # whether they're restricted
    if not (account["privileges"] & ServerPrivileges.UNRESTRICTED):
        response_data += packets.write_account_restricted_packet()

    relations = await relationships.fetch_all(account["account_id"], "friend")
    response_data += packets.write_friends_list_packet(
        [relation["target_id"] for relation in relations]
    )

    # TODO: main menu icon

    logger.info(
        "User login successful",
        account_id=own_osu_session["account_id"],
        osu_session_id=own_osu_session["osu_session_id"],
    )

    return Response(
        content=bytes(response_data),
        headers={"cho-token": str(own_osu_session["osu_session_id"])},
    )


async def handle_bancho_request(request: Request) -> Response:
    # authenticate the request
    osu_session_id = UUID(request.headers["osu-token"])
    osu_session = await osu_sessions.fetch_by_id(osu_session_id)
    if osu_session is None:
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

        await packet_handler(osu_session, packet.packet_data)
        logger.debug("Handled packet", packet_id=packet.packet_id)

    # dequeue all packets to send back to the client
    response_content = bytearray()
    own_packet_bundles = await packet_bundles.dequeue_all(osu_session["osu_session_id"])
    for packet_bundle in own_packet_bundles:
        response_content.extend(packet_bundle["data"])

    # (the session may already be signed out, no worries if so)
    await osu_sessions.partial_update(
        osu_session["osu_session_id"],
        last_communicated_at=datetime.now(),
    )

    return Response(
        content=bytes(response_content),
        headers={"cho-token": str(osu_session["osu_session_id"])},
    )


@bancho_router.post("/")
async def handle_bancho_http_request(request: Request):
    if "osu-token" not in request.headers:
        response = await handle_login(request)
    else:  # they don't have a token
        response = await handle_bancho_request(request)

    return response
