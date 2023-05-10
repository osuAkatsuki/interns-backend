from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

from server import command_handlers
from server import logger
from server import packets
from server import ranking
from server.errors import ServiceError
from server.privileges import ServerPrivileges
from server.repositories import channel_members
from server.repositories import channels
from server.repositories import multiplayer_slots
from server.repositories import packet_bundles
from server.repositories import relationships
from server.repositories import sessions
from server.repositories import spectators
from server.repositories import stats
from server.repositories.multiplayer_matches import MatchStatus
from server.repositories.multiplayer_matches import MatchTeams
from server.repositories.multiplayer_slots import SlotStatus
from server.services import multiplayer_matches

if TYPE_CHECKING:
    from server.repositories.sessions import Session

BanchoHandler = Callable[["Session", bytes], Awaitable[None]]

packet_handlers: dict[packets.ClientPackets, BanchoHandler] = {}


def get_packet_handler(packet_id: packets.ClientPackets):
    return packet_handlers.get(packet_id)


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
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    data = packets.PacketReader(packet_data)

    action = data.read_u8()
    info_text = data.read_string()
    beatmap_md5 = data.read_string()

    mods = data.read_u32()
    mode = data.read_u8()

    beatmap_id = data.read_i32()

    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={
            "action": action,
            "info_text": info_text,
            "beatmap_md5": beatmap_md5,
            "mods": mods,
            "mode": mode,
            "beatmap_id": beatmap_id,
        },
    )
    assert maybe_session is not None
    session = maybe_session

    own_stats = await stats.fetch_one(session["account_id"], mode)
    assert own_stats is not None

    # send the stats update to all active osu sessions' packet bundles
    for other_session in await sessions.fetch_all():
        if other_session["session_id"] == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_user_stats_packet(
                session["account_id"],
                own_presence["action"],
                own_presence["info_text"],
                own_presence["beatmap_md5"],
                own_presence["mods"],
                own_presence["mode"],
                own_presence["beatmap_id"],
                own_stats["ranked_score"],
                own_stats["accuracy"],
                own_stats["play_count"],
                own_stats["total_score"],
                ranking.get_global_rank(session["account_id"]),
                own_stats["performance_points"],
            ),
        )


# SEND_PUBLIC_MESSAGE = 1


@bancho_handler(packets.ClientPackets.SEND_PUBLIC_MESSAGE)
async def send_public_message_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    # read packet data
    packet_reader = packets.PacketReader(packet_data)

    sender_name = packet_reader.read_string()  # always ""
    message_content = packet_reader.read_string()
    recipient_name = packet_reader.read_string()
    sender_id = packet_reader.read_i32()  # always 0

    if len(message_content) > 2000:
        message_content = message_content[:2000] + "..."

    # send message to everyone else
    send_message_packet_data = packets.write_send_message_packet(
        own_presence["username"],
        message_content,
        recipient_name,
        own_presence["account_id"],
    )

    # TODO: send response only to those in the channel
    for other_session in await sessions.fetch_all():
        if other_session["session_id"] == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            other_session["session_id"],
            data=send_message_packet_data,
        )

    # handle commands
    if message_content.startswith("!"):
        trigger, *args = message_content.split(" ")
        command_handler = command_handlers.get_command_handler(trigger)
        if command_handler is not None:
            bancho_bot_message = await command_handler(session, args)
            if bancho_bot_message is not None:
                # TODO: send bancho bot message only to those in the channel
                for other_session in await sessions.fetch_all():
                    await packet_bundles.enqueue(
                        other_session["session_id"],
                        data=packets.write_send_message_packet(
                            sender_name="BanchoBot",
                            message_content=bancho_bot_message,
                            recipient_name=recipient_name,
                            sender_id=0,
                        ),
                    )


# LOGOUT = 2


class ExitReason:
    UPDATE = 1
    QUIT = 2


@bancho_handler(packets.ClientPackets.OSU_EXIT)
async def logout_handler(session: "Session", packet_data: bytes) -> None:
    packet_reader = packets.PacketReader(packet_data)
    reason = packet_reader.read_i32()

    if reason == ExitReason.UPDATE:
        ...
    elif reason == ExitReason.QUIT:
        ...

    own_presence = session["presence"]

    await sessions.delete_by_id(session["session_id"])

    # tell everyone else we logged out
    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        logout_packet_data = packets.write_logout_packet(session["account_id"])
        for other_session in await sessions.fetch_all():
            await packet_bundles.enqueue(
                other_session["session_id"],
                data=logout_packet_data,
            )

    logger.info(
        "User logout successful",
        session_id=session["session_id"],
        account_id=session["account_id"],
    )


# REQUEST_STATUS_UPDATE = 3


@bancho_handler(packets.ClientPackets.REQUEST_STATUS_UPDATE)
async def request_status_update_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    own_stats = await stats.fetch_one(
        session["account_id"],
        own_presence["game_mode"],
    )
    assert own_stats is not None

    await packet_bundles.enqueue(
        session["session_id"],
        packets.write_user_stats_packet(
            own_stats["account_id"],
            own_presence["action"],
            own_presence["info_text"],
            own_presence["beatmap_md5"],
            own_presence["mods"],
            own_presence["game_mode"],
            own_presence["beatmap_id"],
            own_stats["ranked_score"],
            own_stats["accuracy"],
            own_stats["play_count"],
            own_stats["total_score"],
            ranking.get_global_rank(own_stats["account_id"]),
            own_stats["performance_points"],
        ),
    )


# PING = 4


@bancho_handler(packets.ClientPackets.PING)
async def ping_handler(session: "Session", packet_data: bytes):
    # TODO: keep track of each osu! session's last ping time
    pass


# START_SPECTATING = 16


@bancho_handler(packets.ClientPackets.START_SPECTATING)
async def start_spectating_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    packet_reader = packets.PacketReader(packet_data)
    host_account_id = packet_reader.read_i32()

    host_session = await sessions.fetch_by_account_id(host_account_id)

    if host_session is None:
        logger.warning(
            "A user attempted to spectate another user who is offline",
            spectator_id=session["account_id"],
            host_id=host_account_id,
        )
        return

    await spectators.add(
        host_session["session_id"],
        session["session_id"],
    )

    await sessions.partial_update(
        session["session_id"],
        presence={"spectator_host_session_id": host_session["session_id"]},
    )

    await packet_bundles.enqueue(
        host_session["session_id"],
        packets.write_spectator_joined_packet(session["account_id"]),
    )

    for spectator_session_id in await spectators.members(host_session["session_id"]):
        if spectator_session_id == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            spectator_session_id,
            packets.write_fellow_spectator_joined_packet(session["account_id"]),
        )


# STOP_SPECTATING = 17


@bancho_handler(packets.ClientPackets.STOP_SPECTATING)
async def stop_spectating_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    if own_presence["spectator_host_session_id"] is None:
        logger.warning(
            "A user attempted to stop spectating user while not spectating anyone",
            spectator_id=session["account_id"],
        )
        return

    host_session = await sessions.fetch_by_id(own_presence["spectator_host_session_id"])

    if host_session is None:
        logger.warning(
            "A user attempted to stop spectating another user who is offline",
            spectator_id=session["account_id"],
            # host_id=host_session["account_id"], # not possible to eval
        )
        return

    await spectators.remove(
        host_session["session_id"],
        session["session_id"],
    )

    await sessions.partial_update(
        session["session_id"],
        presence={"spectator_host_session_id": None},
    )

    await packet_bundles.enqueue(
        host_session["session_id"],
        packets.write_spectator_left_packet(session["account_id"]),
    )

    for spectator_session_id in await spectators.members(host_session["session_id"]):
        if spectator_session_id == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            spectator_session_id,
            packets.write_fellow_spectator_left_packet(session["account_id"]),
        )


# SPECTATE_FRAMES = 18


@bancho_handler(packets.ClientPackets.SPECTATE_FRAMES)
async def spectate_frames_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    for spectator_session_id in await spectators.members(session["session_id"]):
        await packet_bundles.enqueue(
            spectator_session_id,
            packets.write_spectate_frames_packet(packet_data),
        )


# ERROR_REPORT = 20


# CANT_SPECTATE = 21


@bancho_handler(packets.ClientPackets.CANT_SPECTATE)
async def cant_spectate_handler(session: "Session", packet_data: bytes):
    assert session["presence"] is not None
    
    packet_reader = packets.PacketReader(packet_data)
    host_account_id = packet_reader.read_i32()

    host_session = await sessions.fetch_by_account_id(host_account_id)

    if host_session is None:
        logger.warning(
            "A user attempted to spectate an offline user",
            spectator_id=session["account_id"],
        )
        return

    await packet_bundles.enqueue(
        host_session["session_id"],
        packets.write_spectator_cant_spectate_packet(session["account_id"])
    )

    for spectator_session_id in await spectators.members(host_session["session_id"]):
        if spectator_session_id == session["session_id"]:
            continue
        
        await packet_bundles.enqueue(
            spectator_session_id,
            packets.write_spectator_cant_spectate_packet(session["account_id"]),
        )


# SEND_PRIVATE_MESSAGE = 25


@bancho_handler(packets.ClientPackets.SEND_PRIVATE_MESSAGE)
async def send_private_message_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    packet_reader = packets.PacketReader(packet_data)

    packet_reader.read_string()  # always ""
    message_content = packet_reader.read_string()
    recipient_name = packet_reader.read_string()

    if len(message_content) > 2000:
        message_content = message_content[:2000] + "..."

    recipient_session = await sessions.fetch_by_username(recipient_name)

    if recipient_session is None:
        logger.warning("Recipient is currently offline")
        return

    relationship_info = await relationships.fetch_one(session["account_id"], recipient_session["account_id"])

    if relationship_info is not None and relationship_info["relationship"] == "blocked":
        return

    send_message_packet_data = packets.write_send_message_packet(
        own_presence["username"],
        message_content,
        recipient_name,
        own_presence["account_id"],
    )

    recipient_session = await sessions.fetch_by_username(recipient_name)

    # Todo add notification
    if recipient_session is None:
        return

    await packet_bundles.enqueue(
        recipient_session["session_id"], send_message_packet_data
    )


# PART_LOBBY = 29


# JOIN_LOBBY = 30


# CREATE_MATCH = 31


@bancho_handler(packets.ClientPackets.CREATE_MATCH)
async def create_match_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        await packet_bundles.enqueue(
            session["session_id"],
            data=packets.write_match_join_fail_packet(),
        )
        return

    packet_reader = packets.PacketReader(packet_data)

    osu_match_data = packet_reader.read_osu_match()

    match = await multiplayer_matches.create(
        osu_match_data["match_name"],
        osu_match_data["match_password"],
        osu_match_data["beatmap_name"],
        osu_match_data["beatmap_id"],
        osu_match_data["beatmap_md5"],
        osu_match_data["host_account_id"],
        osu_match_data["game_mode"],
        osu_match_data["mods"],
        osu_match_data["win_condition"],
        osu_match_data["team_type"],
        osu_match_data["freemods_enabled"],
        osu_match_data["random_seed"],
    )
    if isinstance(match, ServiceError):
        logger.error(
            "Failed to create multiplayer match",
            error=match,
            user_id=session["account_id"],
        )
        await packet_bundles.enqueue(
            session["session_id"],
            data=packets.write_match_join_fail_packet(),
        )
        raise RuntimeError("Failed to create multiplayer match")

    slots = []

    our_slot = await multiplayer_slots.create(
        match["match_id"],
        0,  # slot id
        session["account_id"],
        status=SlotStatus.NOT_READY,
        team=MatchTeams.NEUTRAL,
        mods=0,
        loaded=False,
        skipped=False,
    )
    slots.append(our_slot)

    for slot_id in range(1, 16):
        other_slot = await multiplayer_slots.create(
            match["match_id"],
            slot_id,
            account_id=0,
            status=SlotStatus.OPEN,
            team=MatchTeams.NEUTRAL,
            mods=0,
            loaded=False,
            skipped=False,
        )
        slots.append(other_slot)

    lobby_channel = await channels.fetch_one_by_name("#lobby")
    if lobby_channel is None:
        logger.error(
            "Failed to fetch #lobby channel",
            user_id=session["account_id"],
        )
        await packet_bundles.enqueue(
            session["session_id"],
            data=packets.write_match_join_fail_packet(),
        )
        return

    # create two variants of the packet, with and without the password
    # TODO: perhaps consider making a function to (deep)copy & patch the password?
    packet_params = (
        match["match_id"],
        match["status"] == MatchStatus.PLAYING,
        match["mods"],
        match["match_name"],
        match["match_password"],
        match["beatmap_name"],
        match["beatmap_id"],
        match["beatmap_md5"],
        [s["status"] for s in slots],
        [s["team"] for s in slots],
        [s["account_id"] for s in slots if s["status"] & 0b01111100 != 0],
        match["host_account_id"],
        match["game_mode"],
        match["win_condition"],
        match["team_type"],
        match["freemods_enabled"],
        [s["mods"] for s in slots] if match["freemods_enabled"] else [],
        match["random_seed"],
    )

    match_join_success_packet = packets.write_match_join_success_packet(
        *packet_params,
        should_send_password=True,
    )
    await packet_bundles.enqueue(
        session["session_id"],
        match_join_success_packet,
    )

    packet_without_password = packets.write_update_match_packet(
        *packet_params,
        should_send_password=False,
    )

    for other_session_id in await channel_members.members(lobby_channel["channel_id"]):
        if other_session_id == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            other_session_id,
            packet_without_password,
        )


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


@bancho_handler(packets.ClientPackets.CHANNEL_JOIN)
async def user_joins_channel_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    channel_name = packet_reader.read_string()

    channel = await channels.fetch_one_by_name(channel_name)
    if channel is None:
        return

    current_channel_members = await channel_members.members(channel["channel_id"])

    if session["session_id"] in current_channel_members:
        logger.warning(
            "A user attempted to join a channel they are already in",
            user_id=session["account_id"],
            channel_id=channel["channel_id"],
        )
        return

    await channel_members.add(channel["channel_id"], session["session_id"])

    await packet_bundles.enqueue(
        session["session_id"],
        packets.write_channel_join_success_packet(channel["name"]),
    )

    for other_session in await sessions.fetch_all(
        has_any_privilege_bit=channel["read_privileges"]
    ):
        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_channel_info_packet(
                channel["name"],
                channel["topic"],
                len(current_channel_members) + 1,
            ),
        )

    logger.info(
        "User joined channel",
        user_id=session["account_id"],
        channel_name=channel["name"],
    )


# BEATMAP_INFO_REQUEST = 68


# MATCH_TRANSFER_HOST = 70


# FRIEND_ADD = 73


@bancho_handler(packets.ClientPackets.FRIEND_ADD)
async def friend_add_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    target_id = packet_reader.read_i32()

    await relationships.create(
        session["account_id"],
        target_id,
        relationship="friend",
    )


# FRIEND_REMOVE = 74


@bancho_handler(packets.ClientPackets.FRIEND_REMOVE)
async def friend_remove_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    target_id = packet_reader.read_i32()

    await relationships.remove(session["account_id"], target_id)


# MATCH_CHANGE_TEAM = 77


# CHANNEL_PART = 78


@bancho_handler(packets.ClientPackets.CHANNEL_PART)
async def user_leaves_channel_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    channel_name = packet_reader.read_string()

    channel = await channels.fetch_one_by_name(channel_name)
    if channel is None:
        return

    current_channel_members = await channel_members.members(channel["channel_id"])
    if session["session_id"] not in current_channel_members:
        logger.warning(
            "A user attempted to leave a channel they are not in",
            user_id=session["account_id"],
            channel_id=channel["channel_id"],
        )
        return

    await channel_members.remove(channel["channel_id"], session["session_id"])

    # TODO: should we be sending channel_revoked to ourselves?

    for other_session in await sessions.fetch_all(
        has_any_privilege_bit=channel["read_privileges"]
    ):
        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_channel_info_packet(
                channel["name"],
                channel["topic"],
                len(current_channel_members) - 1,
            ),
        )


# RECEIVE_UPDATES = 79


# SET_AWAY_MESSAGE = 82


# IRC_ONLY = 84


# USER_STATS_REQUEST = 85


@bancho_handler(packets.ClientPackets.USER_STATS_REQUEST)
async def user_stats_request_handler(session: "Session", packet_data: bytes) -> None:
    reader = packets.PacketReader(packet_data)

    account_ids = reader.read_i32_list_i16_length()

    for account_id in account_ids:
        if account_id == session["account_id"]:
            continue

        other_session = await sessions.fetch_by_account_id(account_id)
        if other_session is None:
            continue

        other_stats = await stats.fetch_one(
            account_id,
            other_session["presence"]["game_mode"],
        )
        if other_stats is None:
            continue

        await packet_bundles.enqueue(
            session["session_id"],
            data=packets.write_user_stats_packet(
                other_stats["account_id"],
                other_session["presence"]["action"],
                other_session["presence"]["info_text"],
                other_session["presence"]["beatmap_md5"],
                other_session["presence"]["mods"],
                other_session["presence"]["mode"],
                other_session["presence"]["beatmap_id"],
                other_stats["ranked_score"],
                other_stats["accuracy"],
                other_stats["play_count"],
                other_stats["total_score"],
                ranking.get_global_rank(other_stats["account_id"]),
                other_stats["performance_points"],
            ),
        )


# MATCH_INVITE = 87


# MATCH_CHANGE_PASSWORD = 90


# TOURNAMENT_MATCH_INFO_REQUEST = 93


# USER_PRESENCE_REQUEST = 97


# USER_PRESENCE_REQUEST_ALL = 98


# TOGGLE_BLOCK_NON_FRIEND_DMS = 99


# TOURNAMENT_JOIN_MATCH_CHANNEL = 108


# TOURNAMENT_LEAVE_MATCH_CHANNEL = 109
