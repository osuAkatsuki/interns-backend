from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

from server import logger
from server import packets
from server import ranking
from server.repositories import packet_bundles
from server.repositories import sessions
from server.repositories import stats
from server.repositories import channels
from server.repositories import channel_members
from server.repositories import relationships

if TYPE_CHECKING:
    from server.repositories.sessions import Session


packet_handlers = {}


def get_packet_handler(packet_id: packets.ClientPackets):
    return packet_handlers.get(packet_id)


BanchoHandler = Callable[["Session", bytes], Awaitable[None]]


def bancho_handler(
    packet_id: packets.ClientPackets,
) -> Callable[[BanchoHandler], BanchoHandler]:
    def wrapper(f: BanchoHandler) -> BanchoHandler:
        packet_handlers[packet_id] = f
        return f

    return wrapper


# CHANGE_ACTION = 0


@bancho_handler(packets.ClientPackets.CHANGE_ACTION)
async def change_action_handler(session: "Session", packet_data: bytes):
    assert session["presence"] is not None

    data = packets.PacketReader(packet_data)

    action = data.read_u8()
    info_text = data.read_string()
    map_md5 = data.read_string()

    mods = data.read_u32()
    mode = data.read_u8()

    map_id = data.read_i32()

    maybe_session = await sessions.update_by_id(
        session["session_id"],
        presence={
            "action": action,
            "info_text": info_text,
            "map_md5": map_md5,
            "mods": mods,
            "mode": mode,
            "map_id": map_id,
        },
    )
    assert maybe_session is not None
    session = maybe_session

    assert session["presence"] is not None

    # TODO: only when not restricted

    session_stats = await stats.fetch_one(session["account_id"], mode)
    assert session_stats is not None

    # send the stats update to all active osu sessions' packet bundles
    for other_session in await sessions.fetch_all(osu_clients_only=True):
        # if other_session["session_id"] == session["session_id"]:
        #     continue

        assert other_session["presence"] is not None

        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_user_stats_packet(
                session["account_id"],
                session["presence"]["action"],
                session["presence"]["info_text"],
                session["presence"]["beatmap_md5"],
                session["presence"]["mods"],
                session["presence"]["mode"],
                session["presence"]["beatmap_id"],
                session_stats["ranked_score"],
                session_stats["accuracy"],
                session_stats["play_count"],
                session_stats["total_score"],
                ranking.get_global_rank(session["account_id"]),
                session_stats["performance_points"],
            ),
        )


# SEND_PUBLIC_MESSAGE = 1


@bancho_handler(packets.ClientPackets.SEND_PUBLIC_MESSAGE)
async def send_public_message_handler(session: "Session", packet_data: bytes):
    assert session["presence"] is not None

    # read packet data
    packet_reader = packets.PacketReader(packet_data)

    # TODO: why am i getting "" for sender_name?
    # TODO: why am i getting 0 for sender_id?
    sender_name = packet_reader.read_string()
    message_content = packet_reader.read_string()
    recipient_name = packet_reader.read_string()
    sender_id = packet_reader.read_i32()

    # send message to everyone else
    send_message_packet_data = packets.write_send_message_packet(
        session["presence"]["username"],
        message_content,
        recipient_name,
        session["presence"]["account_id"],
    )

    for other_session in await sessions.fetch_all(osu_clients_only=True):
        if other_session["session_id"] == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            other_session["session_id"],
            data=send_message_packet_data,
        )


# LOGOUT = 2


@bancho_handler(packets.ClientPackets.LOGOUT)
async def logout_handler(session: "Session", packet_data: bytes) -> None:
    await sessions.delete_by_id(session["session_id"])

    # tell everyone else we logged out
    logout_packet_data = packets.write_logout_packet(session["account_id"])
    for other_session in await sessions.fetch_all():
        await packet_bundles.enqueue(
            other_session["session_id"],
            data=logout_packet_data,
        )

    logger.info(
        "Log out successful",
        session_id=session["session_id"],
        account_id=session["account_id"],
    )


# REQUEST_STATUS_UPDATE = 3


@bancho_handler(packets.ClientPackets.REQUEST_STATUS_UPDATE)
async def request_status_update_handler(session: "Session", packet_data: bytes):
    assert session["presence"] is not None

    own_stats = await stats.fetch_one(
        session["account_id"],
        session["presence"]["game_mode"],
    )
    assert own_stats is not None

    await packet_bundles.enqueue(
        session["session_id"],
        packets.write_user_stats_packet(
            own_stats["account_id"],
            session["presence"]["action"],
            session["presence"]["info_text"],
            session["presence"]["beatmap_md5"],
            session["presence"]["mods"],
            session["presence"]["game_mode"],
            session["presence"]["beatmap_id"],
            own_stats["ranked_score"],
            own_stats["accuracy"],
            own_stats["play_count"],
            own_stats["total_score"],
            ranking.get_global_rank(own_stats["account_id"]),
            own_stats["performance_points"],
        ),
    )


@bancho_handler(packets.ClientPackets.CHANNEL_PART)
async def user_leaves_channel_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    channel_name = packet_reader.read_string()

    channel = await channels.fetch_one_by_name(channel_name)

    if not channel:
        return

    await channel_members.remove(channel["channel_id"], session["session_id"])


@bancho_handler(packets.ClientPackets.CHANNEL_JOIN)
async def user_joins_channel_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    channel_name = packet_reader.read_string()

    channel = await channels.fetch_one_by_name(channel_name)

    if not channel:
        return

    channel_members = await channel_members.members(channel["channel_id"])

    if session["session_id"] in channel_members :
        return

    await channel_members.add(channel["channel_id"], session["session_id"])


@bancho_handler(packets.ClientPackets.FRIEND_ADD)
async def user_adds_friend_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    target_id = packet_reader.read_i32()

    await relationships.create(session["account_id"], target_id, "friend")


@bancho_handler(packets.ClientPackets.FRIEND_REMOVE)
async def user_removes_friend_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    user_being_unfriended_id = packet_reader.read_i32()

    await relationships.remove(session["account_id"], user_being_unfriended_id)


@bancho_handler(packets.ClientPackets.SEND_PRIVATE_MESSAGE)
async def send_private_message_handler(session: "Session", packet_data: bytes):
    pass


# TOGGLE BLOCK NON FRIEND DMS WRITTEN TWICE IN PACKETS


# PING = 4


@bancho_handler(packets.ClientPackets.PING)
async def ping_handler(session: "Session", packet_data: bytes):
    # TODO: keep track of each osu! session's last ping time
    pass


# START_SPECTATING = 16


# STOP_SPECTATING = 17


# SPECTATE_FRAMES = 18


# ERROR_REPORT = 20


# CANT_SPECTATE = 21


# SEND_PRIVATE_MESSAGE = 25


# PART_LOBBY = 29


# JOIN_LOBBY = 30


# CREATE_MATCH = 31


# JOIN_MATCH = 32


# PART_MATCH = 33


# MATCH_CHANGE_SLOT = 38


# MATCH_READY = 39


# MATCH_LOCK = 40


# MATCH_CHANGE_SETTINGS = 41


# MATCH_START = 44


# MATCH_SCORE_UPDATE = 47


# MATCH_COMPLETE = 49


# MATCH_CHANGE_MODS = 51


# MATCH_LOAD_COMPLETE = 52


# MATCH_NO_BEATMAP = 54


# MATCH_NOT_READY = 55


# MATCH_FAILED = 56


# MATCH_HAS_BEATMAP = 59


# MATCH_SKIP_REQUEST = 60


# CHANNEL_JOIN = 63


# BEATMAP_INFO_REQUEST = 68


# MATCH_TRANSFER_HOST = 70


# FRIEND_ADD = 73


# FRIEND_REMOVE = 74


# MATCH_CHANGE_TEAM = 77


# CHANNEL_PART = 78


# RECEIVE_UPDATES = 79


# SET_AWAY_MESSAGE = 82


# IRC_ONLY = 84


# USER_STATS_REQUEST = 85


# MATCH_INVITE = 87


# MATCH_CHANGE_PASSWORD = 90


# TOURNAMENT_MATCH_INFO_REQUEST = 93


# USER_PRESENCE_REQUEST = 97


# USER_PRESENCE_REQUEST_ALL = 98


# TOGGLE_BLOCK_NON_FRIEND_DMS = 99


# TOURNAMENT_JOIN_MATCH_CHANNEL = 108


# TOURNAMENT_LEAVE_MATCH_CHANNEL = 109
