from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING
from uuid import UUID

from app import clients
from app import commands
from app import game_modes
from app import logger
from app import packets
from app import ranking
from app.errors import ServiceError
from app.game_modes import GameMode
from app.mods import filter_invalid_mod_combinations
from app.mods import Mods
from app.privileges import ServerPrivileges
from app.repositories import channel_members
from app.repositories import channels
from app.repositories import multiplayer_slots
from app.repositories import packet_bundles
from app.repositories import relationships
from app.repositories import sessions
from app.repositories import spectators
from app.repositories import stats
from app.repositories.multiplayer_matches import MatchStatus
from app.repositories.multiplayer_matches import MatchTeams
from app.repositories.multiplayer_matches import MatchTeamTypes
from app.repositories.multiplayer_slots import SlotStatus
from app.repositories.sessions import Action
from app.services import multiplayer_matches

if TYPE_CHECKING:
    from app.repositories.sessions import Presence, Session

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
    vanilla_game_mode = data.read_u8()

    beatmap_id = data.read_i32()

    # XXX: this is a quirk of the osu! client, where it adjusts this value
    # only after it sends the packet to the server; so we need to adjust
    mods = filter_invalid_mod_combinations(mods, vanilla_game_mode)

    game_mode = game_modes.for_server(vanilla_game_mode, mods)

    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={
            "action": action,
            "info_text": info_text,
            "beatmap_md5": beatmap_md5,
            "mods": mods,
            "game_mode": game_mode,
            "beatmap_id": beatmap_id,
        },
    )
    assert maybe_session is not None
    session = maybe_session

    own_stats = await stats.fetch_one(session["account_id"], game_mode)
    assert own_stats is not None

    own_global_rank = await ranking.get_global_rank(session["account_id"], game_mode)

    # send the stats update to all active osu sessions' packet bundles
    for other_session in await sessions.fetch_all():
        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_user_stats_packet(
                session["account_id"],
                own_presence["action"],
                own_presence["info_text"],
                own_presence["beatmap_md5"],
                own_presence["mods"],
                vanilla_game_mode,
                own_presence["beatmap_id"],
                own_stats["ranked_score"],
                own_stats["accuracy"],
                own_stats["play_count"],
                own_stats["total_score"],
                own_global_rank,
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

    if recipient_name == "#multiplayer":
        multiplayer_match_id = session["presence"]["multiplayer_match_id"]
        if multiplayer_match_id is None:
            logger.warning(
                "User tried to send a message in #multiplayer without being in a match",
                account_id=session["account_id"],
            )
            return

        channel_name = f"#mp_{multiplayer_match_id}"
    # TODO: spectator
    else:
        channel_name = recipient_name

    channel = await channels.fetch_one_by_name(channel_name)

    if channel is None:
        logger.warning(
            "User tried to join channel when it doesn't exist",
            channel_name=channel_name,
            recipient_name=recipient_name,
            account_id=session["account_id"],
        )
        return

    if len(message_content) > 2000:
        message_content = message_content[:2000] + "..."

    # send message to everyone else
    send_message_packet_data = packets.write_send_message_packet(
        own_presence["username"],
        message_content,
        recipient_name,
        own_presence["account_id"],
    )

    if message_content.startswith("!help"):
        target_session_ids = []
    else:
        target_session_ids = await channel_members.members(channel["channel_id"])

    for other_session_id in target_session_ids:
        if other_session_id == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            other_session_id,
            data=send_message_packet_data,
        )

    # handle commands
    if message_content.startswith("!"):
        trigger, *args = message_content.split(" ")
        command = commands.get_command(trigger)
        if command is not None:
            if command.privileges is not None:
                if not own_presence["privileges"] & command.privileges:
                    return

            bancho_bot_message = await command.callback(session, args)

            # send message to everyone else
            if bancho_bot_message is not None:
                if message_content.startswith("!help"):
                    # XXX: the osu! client seems to have a special case for this,
                    # where it will dm the player. if we don't have this case,
                    # this message will be DMed to all players in the channel
                    target_session_ids = [session["session_id"]]
                else:
                    target_session_ids = await channel_members.members(
                        channel["channel_id"]
                    )

                for other_session_id in target_session_ids:
                    await packet_bundles.enqueue(
                        other_session_id,
                        data=packets.write_send_message_packet(
                            sender_name="BanchoBot",
                            message_content=bancho_bot_message,
                            recipient_name=recipient_name,
                            sender_id=0,
                        ),
                    )


# LOGOUT = 2


class ExitReason:
    UPDATE = 0
    QUIT = 1


@bancho_handler(packets.ClientPackets.OSU_EXIT)
async def logout_handler(session: "Session", packet_data: bytes) -> None:
    packet_reader = packets.PacketReader(packet_data)
    reason = packet_reader.read_i32()

    if reason == ExitReason.UPDATE:
        pass
    elif reason == ExitReason.QUIT:
        pass
    else:
        logger.warning(
            "User sent invalid exit reason on logout",
            reason=reason,
            account_id=session["account_id"],
        )

    own_presence = session["presence"]

    await sessions.delete_by_id(session["session_id"])

    # TODO: spectator
    # TODO: multiplayer
    # TODO: channels

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

    vanilla_game_mode = game_modes.for_client(own_presence["game_mode"])

    own_global_rank = await ranking.get_global_rank(
        session["account_id"],
        own_presence["game_mode"],
    )

    await packet_bundles.enqueue(
        session["session_id"],
        packets.write_user_stats_packet(
            own_stats["account_id"],
            own_presence["action"],
            own_presence["info_text"],
            own_presence["beatmap_md5"],
            own_presence["mods"],
            vanilla_game_mode,
            own_presence["beatmap_id"],
            own_stats["ranked_score"],
            own_stats["accuracy"],
            own_stats["play_count"],
            own_stats["total_score"],
            own_global_rank,
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

    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"spectator_host_session_id": host_session["session_id"]},
    )
    assert maybe_session is not None
    session = maybe_session

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

    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"spectator_host_session_id": None},
    )
    assert maybe_session is not None
    session = maybe_session

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

    if session["presence"]["spectator_host_session_id"] is None:
        logger.warning(
            "A user told us they can't spectate while not spectating anyone",
            spectator_id=session["account_id"],
        )
        return

    host_session_id = session["presence"]["spectator_host_session_id"]

    host_session = await sessions.fetch_by_id(host_session_id)
    if host_session is None:
        logger.warning(
            "A user told us they can't spectate another user who is offline",
            spectator_id=session["account_id"],
            host_id=host_session_id,
        )
        return

    packet_data = packets.write_spectator_cant_spectate_packet(session["account_id"])

    await packet_bundles.enqueue(host_session["session_id"], packet_data)

    for spectator_session_id in await spectators.members(host_session["session_id"]):
        await packet_bundles.enqueue(spectator_session_id, packet_data)


# SEND_PRIVATE_MESSAGE = 25


@bancho_handler(packets.ClientPackets.SEND_PRIVATE_MESSAGE)
async def send_private_message_handler(session: "Session", packet_data: bytes):
    own_presence = session["presence"]

    if not own_presence["privileges"] & ServerPrivileges.UNRESTRICTED:
        return

    packet_reader = packets.PacketReader(packet_data)

    sender_name = packet_reader.read_string()  # always ""
    message_content = packet_reader.read_string()
    recipient_name = packet_reader.read_string()
    sender_id = packet_reader.read_i32()  # always 0

    if len(message_content) > 2000:
        message_content = message_content[:2000] + "..."

    recipient_session = await sessions.fetch_by_username(recipient_name)

    if recipient_session is None:
        logger.warning(
            "Recipient session could not be found by username.",
            recipient_name=recipient_name,
        )
        return

    relationship_info = await relationships.fetch_one(
        session["account_id"], recipient_session["account_id"]
    )

    if relationship_info is not None and relationship_info["relationship"] == "blocked":
        return

    recipient_presence = recipient_session["presence"]

    # if the recipient is afk and has a away message, send to self
    if (
        recipient_presence["action"] == Action.AFK
        and recipient_presence["away_message"] is not None
    ):
        away_message_packet_data = packets.write_send_message_packet(
            recipient_presence["username"],
            recipient_presence["away_message"],
            own_presence["username"],
            recipient_session["account_id"],
        )

        await packet_bundles.enqueue(session["session_id"], away_message_packet_data)

    send_message_packet_data = packets.write_send_message_packet(
        own_presence["username"],
        message_content,
        recipient_name,
        own_presence["account_id"],
    )

    await packet_bundles.enqueue(
        recipient_session["session_id"], send_message_packet_data
    )


# PART_LOBBY = 29


@bancho_handler(packets.ClientPackets.PART_LOBBY)
async def part_lobby_handler(session: "Session", packet_data: bytes):
    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"receive_match_updates": False},
    )
    assert maybe_session is not None
    session = maybe_session

    channel = await channels.fetch_one_by_name("#lobby")
    assert channel

    await channel_members.remove(
        channel_id=channel["channel_id"],
        session_id=session["session_id"],
    )

    current_channel_members = await channel_members.members(channel["channel_id"])

    for other_session in await sessions.fetch_all(
        has_any_privilege_bit=channel["read_privileges"]
    ):
        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_channel_info_packet(
                channel["name"],
                channel["topic"],
                len(current_channel_members),
            ),
        )


# JOIN_LOBBY = 30


@bancho_handler(packets.ClientPackets.JOIN_LOBBY)
async def join_lobby_handler(session: "Session", packet_data: bytes):
    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"receive_match_updates": True},
    )
    assert maybe_session is not None
    session = maybe_session

    matches = await multiplayer_matches.fetch_all()
    assert not isinstance(matches, ServiceError)

    for match in matches:
        slots = await multiplayer_slots.fetch_all(match["match_id"])

        vanilla_game_mode = game_modes.for_client(match["game_mode"])
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
            vanilla_game_mode,
            match["win_condition"],
            match["team_type"],
            match["freemods_enabled"],
            [s["mods"] for s in slots] if match["freemods_enabled"] else [],
            match["random_seed"],
        )

        match_packet = packets.write_update_match_packet(
            *packet_params,
            should_send_password=False,
        )

        await packet_bundles.enqueue(
            session_id=session["session_id"],
            data=match_packet,
        )


# CREATE_MATCH = 31


async def _broadcast_to_match(
    match_id: int,
    data: bytes,
    slot_flags: int,
):
    match = await multiplayer_matches.fetch_one(match_id)
    assert not isinstance(match, ServiceError)

    slots = await multiplayer_slots.fetch_all(match["match_id"])

    for slot in slots:
        if slot["account_id"] == -1 or (slot["status"] & slot_flags) == 0:
            continue

        await packet_bundles.enqueue(
            slot["session_id"],
            data,
        )


async def _broadcast_to_lobby(data: bytes):
    lobby_channel = await channels.fetch_one_by_name("#lobby")
    if lobby_channel is None:
        logger.error(
            "Failed to fetch #lobby channel",
        )
        return False

    for session_id in await channel_members.members(lobby_channel["channel_id"]):
        await packet_bundles.enqueue(
            session_id,
            data,
        )


# XXX: this is a helper for some code that is repeated several times
# throughout a multiplayer implementation - broadcasting state changes
async def _broadcast_match_updates(
    match_id: int,
    send_to_lobby: bool = True,
):
    match = await multiplayer_matches.fetch_one(match_id)
    assert not isinstance(match, ServiceError)

    slots = await multiplayer_slots.fetch_all(match["match_id"])

    vanilla_game_mode = game_modes.for_client(match["game_mode"])

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
        vanilla_game_mode,
        match["win_condition"],
        match["team_type"],
        match["freemods_enabled"],
        [s["mods"] for s in slots] if match["freemods_enabled"] else [],
        match["random_seed"],
    )

    # send the match data (with password) to those in the multiplayer match
    match_packet = packets.write_update_match_packet(
        *packet_params,
        should_send_password=True,
    )

    await _broadcast_to_match(
        match_id=match_id,
        data=match_packet,
        slot_flags=SlotStatus.HAS_PLAYER,
    )

    if send_to_lobby:
        match_packet = packets.write_update_match_packet(
            *packet_params,
            should_send_password=False,
        )

        await _broadcast_to_lobby(match_packet)


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

    vanilla_game_mode = osu_match_data["game_mode"]
    game_mode = game_modes.for_server(
        osu_match_data["game_mode"],
        own_presence["mods"],
    )

    # if we are spectating someone, stop spectating them
    if own_presence["spectator_host_session_id"] is not None:
        host_session = await sessions.fetch_by_id(
            own_presence["spectator_host_session_id"]
        )

        if host_session is None:
            logger.warning(
                "A user attempted to stop spectating another user who is offline",
                spectator_id=session["account_id"],
                # host_id=host_session["account_id"], # not possible to eval
            )
            return

        # remove us from the host's spectators
        spectator = await spectators.remove(
            host_session["session_id"],
            session["session_id"],
        )
        assert spectator is not None

        # remove the host from our presence
        maybe_session = await sessions.partial_update(
            session["session_id"],
            presence={"spectator_host_session_id": None},
        )
        assert maybe_session is not None
        session = maybe_session

        # inform the host that we left
        await packet_bundles.enqueue(
            host_session["session_id"],
            packets.write_spectator_left_packet(session["account_id"]),
        )

        # inform the other spectators that we left
        for spectator_session_id in await spectators.members(
            host_session["session_id"]
        ):
            if spectator_session_id == session["session_id"]:
                continue

            await packet_bundles.enqueue(
                spectator_session_id,
                packets.write_fellow_spectator_left_packet(session["account_id"]),
            )

    # create the multiplayer match
    match = await multiplayer_matches.create(
        osu_match_data["match_name"],
        osu_match_data["match_password"],
        osu_match_data["beatmap_name"],
        osu_match_data["beatmap_id"],
        osu_match_data["beatmap_md5"],
        osu_match_data["host_account_id"],
        game_mode,
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
        return

    # create the #multiplayer chat
    match_channel = await channels.create(
        name=f"#mp_{match['match_id']}",
        topic=f"Channel for multiplayer match ID {match['match_id']}",
        read_privileges=ServerPrivileges.UNRESTRICTED,
        write_privileges=ServerPrivileges.UNRESTRICTED,
        auto_join=False,
        temporary=True,
    )

    # claim a slot for the session
    async with await clients.redlock.lock(f"slot_ids:lock:{match['match_id']}"):
        slot_id = await multiplayer_slots.claim_slot_id(match["match_id"])
        if slot_id is None:
            logger.error(
                "Failed to claim slot",
                session_id=session["session_id"],
                match_id=match["match_id"],
            )
            await packet_bundles.enqueue(
                session["session_id"],
                data=packets.write_match_join_fail_packet(),
            )
            return

        await multiplayer_slots.partial_update(
            match["match_id"],
            slot_id,
            account_id=session["account_id"],
            session_id=session["session_id"],
            status=multiplayer_slots.SlotStatus.NOT_READY,
        )

    # join the multiplayer match
    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"multiplayer_match_id": match["match_id"]},
    )
    assert maybe_session is not None
    session = maybe_session

    # join the #multiplayer channel
    await channel_members.add(match_channel["channel_id"], session["session_id"])

    # inform our user of the #multiplayer channel
    await packet_bundles.enqueue(
        session["session_id"],
        data=(
            packets.write_channel_auto_join_packet(
                name="#multiplayer",
                topic=match_channel["topic"],
                num_sessions=1,
            )
            + packets.write_channel_join_success_packet(channel_name="#multiplayer")
        ),
    )

    slots = await multiplayer_slots.fetch_all(match["match_id"])

    # send the match data (with password) to the creator
    match_join_success_packet = packets.write_match_join_success_packet(
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
        vanilla_game_mode,
        match["win_condition"],
        match["team_type"],
        match["freemods_enabled"],
        [s["mods"] for s in slots] if match["freemods_enabled"] else [],
        match["random_seed"],
        should_send_password=True,
    )
    await packet_bundles.enqueue(
        session["session_id"],
        match_join_success_packet,
    )

    # add the creator as host
    # TODO: does this make sense over initially creating the match with the user as host?
    match = await multiplayer_matches.partial_update(
        match_id=match["match_id"],
        host_account_id=session["account_id"],
    )
    assert not isinstance(match, ServiceError)

    await _broadcast_match_updates(match["match_id"])


# JOIN_MATCH = 32


@bancho_handler(packets.ClientPackets.JOIN_MATCH)
async def join_match_handler(session: "Session", packet_data: bytes) -> None:
    reader = packets.PacketReader(packet_data)

    match_id = reader.read_i32()
    match_password = reader.read_string()

    # attempt to find the match we are trying to join
    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "Failed to find match when joining",
            session_id=session["session_id"],
            match_id=match_id,
        )
        await packet_bundles.enqueue(
            session["session_id"],
            packets.write_match_join_fail_packet(),
        )
        return

    # if the match has a non-empty password, validate the client got it right
    if match["match_password"] != "" and match_password != match["match_password"]:
        logger.warning(
            "User tried to join a match with an incorrect password",
            session_id=session["session_id"],
            match_id=match_id,
        )
        await packet_bundles.enqueue(
            session["session_id"],
            packets.write_match_join_fail_packet(),
        )
        return

    # claim a slot for the session
    async with await clients.redlock.lock(f"slot_ids:lock:{match_id}"):
        slot_id = await multiplayer_slots.claim_slot_id(match_id)
        if slot_id is None:
            logger.error(
                "Failed to claim slot",
                session_id=session["session_id"],
                match_id=match_id,
            )
            await packet_bundles.enqueue(
                session["session_id"],
                packets.write_match_join_fail_packet(),
            )
            return

        await multiplayer_slots.partial_update(
            match_id,
            slot_id,
            account_id=session["account_id"],
            session_id=session["session_id"],
            status=multiplayer_slots.SlotStatus.NOT_READY,
        )

    # join the multiplayer match
    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"multiplayer_match_id": match_id},
    )
    assert maybe_session is not None
    session = maybe_session

    match_channel = await channels.fetch_one_by_name(f"#mp_{match_id}")
    assert match_channel is not None

    # join the #multiplayer channel
    await channel_members.add(match_channel["channel_id"], session["session_id"])
    match_channel_members = await channel_members.members(match_channel["channel_id"])

    # inform our user of the #multiplayer channel
    await packet_bundles.enqueue(
        session["session_id"],
        data=(
            packets.write_channel_auto_join_packet(
                name="#multiplayer",
                topic=match_channel["topic"],
                num_sessions=len(match_channel_members),
            )
            + packets.write_channel_join_success_packet("#multiplayer")
        ),
    )

    slots = await multiplayer_slots.fetch_all(match["match_id"])

    vanilla_game_mode = game_modes.for_client(match["game_mode"])

    # send the match data (with password) to the creator
    match_join_success_packet = packets.write_match_join_success_packet(
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
        vanilla_game_mode,
        match["win_condition"],
        match["team_type"],
        match["freemods_enabled"],
        [s["mods"] for s in slots] if match["freemods_enabled"] else [],
        match["random_seed"],
        should_send_password=True,
    )
    await packet_bundles.enqueue(
        session["session_id"],
        match_join_success_packet,
    )

    # make other people aware the session joined
    await _broadcast_match_updates(match_id)

    logger.info(
        "User joined a match",
        session_id=session["session_id"],
        match_id=match_id,
    )


# PART_MATCH = 33


@bancho_handler(packets.ClientPackets.PART_MATCH)
async def part_match_handler(session: "Session", packet_data: bytes) -> None:
    own_presence = session["presence"]

    if own_presence["multiplayer_match_id"] is None:
        logger.warning(
            "User tried to leave a match while not in a match",
            session_id=session["session_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(own_presence["multiplayer_match_id"])
    if isinstance(match, ServiceError):
        logger.error(
            "Failed to find match when leaving",
            session_id=session["session_id"],
            match_id=own_presence["multiplayer_match_id"],
        )
        return

    current_slot = await multiplayer_slots.fetch_one_by_session_id(
        match["match_id"],
        session["session_id"],
    )
    assert current_slot is not None

    # open up old slot
    current_slot = await multiplayer_slots.partial_update(
        match["match_id"],
        current_slot["slot_id"],
        account_id=-1,
        session_id=UUID(int=0),
        status=SlotStatus.OPEN,
        team=MatchTeams.NEUTRAL,
        mods=0,
        loaded=False,
        skipped=False,
    )
    assert current_slot is not None

    match_channel = await channels.fetch_one_by_name(f"#mp_{match['match_id']}")
    assert match_channel is not None

    if match["host_account_id"] == session["account_id"]:
        # if the host left, pick a new host
        slots = await multiplayer_slots.fetch_all(match["match_id"])

        new_host_slot = None
        for slot in slots:
            # slot doesn't have a user
            if slot["account_id"] == -1:
                continue

            new_host_slot = slot
            break

        # no one is left in the match, close it
        if new_host_slot is None:
            lobby_channel = await channels.fetch_one_by_name("#lobby")
            assert lobby_channel is not None

            # inform everyone in the lobby that the match no longer exists
            for other_session_id in await channel_members.members(
                lobby_channel["channel_id"]
            ):
                await packet_bundles.enqueue(
                    other_session_id,
                    packets.write_dispose_match_packet(match["match_id"]),
                )

            # kick everyone out of the multiplayer match and channel
            for other_session_id in await channel_members.members(
                match_channel["channel_id"]
            ):
                await packet_bundles.enqueue(
                    other_session_id,
                    data=(
                        packets.write_dispose_match_packet(match["match_id"])
                        + packets.write_channel_kick_packet("#multiplayer")
                    ),
                )
                await channel_members.remove(
                    match_channel["channel_id"],
                    other_session_id,
                )

            # delete the multiplayer channel and it's slots
            match = await multiplayer_matches.delete(match["match_id"])
            assert not isinstance(match, ServiceError)

            # delete the multiplayer channel
            match_channel = await channels.delete(match_channel["channel_id"])
            assert not isinstance(match_channel, ServiceError)

            logger.info(
                "Match closed due to no members",
                match_id=match["match_id"],
            )

            return

        await multiplayer_matches.partial_update(
            match_id=match["match_id"],
            host_account_id=new_host_slot["account_id"],
        )

        await packet_bundles.enqueue(
            new_host_slot["session_id"],
            packets.write_match_transfer_host_packet(),
        )

        logger.info(
            "Match host passed to new user",
            old_host_session_id=session["session_id"],
            new_host_session_id=new_host_slot["session_id"],
            match_id=match["match_id"],
        )

    # leave the multiplayer channel
    await channel_members.remove(match_channel["channel_id"], session["session_id"])
    await packet_bundles.enqueue(
        session["session_id"],
        packets.write_channel_kick_packet("#multiplayer"),
    )

    # inform relevant places of the new match state
    await _broadcast_match_updates(match["match_id"])

    logger.info(
        "User left a match",
        session_id=session["session_id"],
        match_id=match["match_id"],
    )


# MATCH_CHANGE_SLOT = 38


@bancho_handler(packets.ClientPackets.MATCH_CHANGE_SLOT)
async def match_change_slot_handler(session: "Session", packet_data: bytes) -> None:
    own_presence = session["presence"]

    reader = packets.PacketReader(packet_data)

    slot_id = reader.read_i32()

    match_id = own_presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "User tried to change slot while not in a match",
            account_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "Failed to find match when changing slot",
            match_id=match_id,
            account_id=session["account_id"],
            target_slot_id=slot_id,
        )
        return

    current_slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id,
        session["session_id"],
    )
    if current_slot is None:
        logger.warning(
            "User not inside of a slot",
            account_id=session["account_id"],
            match_id=match_id,
        )
        return

    target_slot = await multiplayer_slots.fetch_one(match_id, slot_id)
    if target_slot is None:
        logger.warning(
            "User tried to change to a slot that doesn't exist",
            match_id=match_id,
            account_id=session["account_id"],
            slot_id=slot_id,
        )
        return

    if target_slot["status"] != SlotStatus.OPEN:
        logger.warning(
            "User tried to change to a slot that isn't open",
            match_id=match_id,
            account_id=session["account_id"],
            slot_id=slot_id,
        )
        return

    # switch to new slot
    target_slot = await multiplayer_slots.partial_update(
        match_id,
        slot_id,
        account_id=current_slot["account_id"],
        session_id=current_slot["session_id"],
        status=current_slot["status"],
        team=current_slot["team"],
        mods=current_slot["mods"],
        loaded=current_slot["loaded"],
        skipped=current_slot["skipped"],
    )
    assert target_slot is not None

    # open up old slot
    current_slot = await multiplayer_slots.partial_update(
        match_id,
        current_slot["slot_id"],
        account_id=-1,
        session_id=UUID(int=0),
        status=SlotStatus.OPEN,
        team=MatchTeams.NEUTRAL,
        mods=0,
        loaded=False,
        skipped=False,
    )
    assert current_slot is not None

    logger.info(
        "User changed slot",
        old_slot_id=current_slot["slot_id"],
        new_slot_id=slot_id,
        match_id=match_id,
        account_id=session["account_id"],
    )

    # send updated data to those in the multi match, and #lobby
    await _broadcast_match_updates(match["match_id"])


# MATCH_READY = 39


@bancho_handler(packets.ClientPackets.MATCH_READY)
async def match_ready_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to get ready but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to get ready but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    if slot["status"] != SlotStatus.NOT_READY:
        logger.warning(
            "A user attempted to get ready but they are not allowed to.",
            user_id=session["account_id"],
            match_id=match_id,
            slot_id=slot["slot_id"],
            slot_status=slot["status"],
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        status=SlotStatus.READY,
    )

    await _broadcast_match_updates(match_id)


# MATCH_LOCK = 40


@bancho_handler(packets.ClientPackets.MATCH_LOCK)
async def match_lock_handler(session: "Session", packet_data: bytes):
    reader = packets.PacketReader(packet_data)
    slot_id = reader.read_i32()

    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to (un)lock a slot but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to (un)lock a slot but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    # only the host can edit slots
    if match["host_account_id"] != session["account_id"]:
        logger.warning(
            "A user attempted to (un)lock a slot but they are not the host.",
            user_id=session["account_id"],
            match_id=match_id,
            match_host=match["host_account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one(
        match_id=match_id,
        slot_id=slot_id,
    )
    if not slot:
        logger.warning(
            "A user attempted to (un)lock a slot that does not exist.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    if slot["account_id"] != -1:
        if slot["account_id"] == session["account_id"]:
            logger.warning(
                "A user attempted to lock their own slot.",
                user_id=session["account_id"],
                match_id=match_id,
            )
            return

        slot_session = await sessions.fetch_by_account_id(slot["account_id"])
        assert slot_session is not None

        match_channel = await channels.fetch_one_by_name(f"#mp_{match_id}")
        assert match_channel is not None

        await channel_members.remove(
            channel_id=match_channel["channel_id"],
            session_id=slot_session["session_id"],
        )

        await packet_bundles.enqueue(
            session_id=slot_session["session_id"],
            data=packets.write_channel_kick_packet("#multiplayer"),
        )

        logger.info(
            "User was kicked from match.",
            host_id=session["account_id"],
            target_id=slot_session["account_id"],
            match_id=match_id,
        )

    if slot["status"] == SlotStatus.LOCKED:
        new_status = SlotStatus.OPEN
    else:
        new_status = SlotStatus.LOCKED

    # lock slot
    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        account_id=-1,
        session_id=UUID(int=0),
        status=new_status,
        team=MatchTeams.NEUTRAL,
        mods=0,
        loaded=False,
        skipped=False,
    )

    # inform relevant places of the new match state
    await _broadcast_match_updates(match_id)

    logger.info(
        "User (un)locked match slot.",
        host_id=session["account_id"],
        slot_id=slot_id,
        match_id=match_id,
    )


# MATCH_CHANGE_SETTINGS = 41


@bancho_handler(packets.ClientPackets.MATCH_CHANGE_SETTINGS)
async def match_change_settings_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to change match settings but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to change match settings but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    # only the host can change match settings
    if match["host_account_id"] != session["account_id"]:
        logger.warning(
            "A user attempted to change match settings but they are not the host.",
            user_id=session["account_id"],
            match_id=match_id,
            match_host=match["host_account_id"],
        )
        return

    packet_reader = packets.PacketReader(packet_data)
    osu_match_data = packet_reader.read_osu_match()

    vanilla_game_mode = osu_match_data["game_mode"]
    game_mode = game_modes.for_server(
        vanilla_game_mode,
        match["mods"],
    )

    slots = await multiplayer_slots.fetch_all(match_id)
    need_slot_updates = False
    # if we switch to a versus mode, split all players into teams
    if osu_match_data["team_type"] != match["team_type"] and osu_match_data[
        "team_type"
    ] in (MatchTeamTypes.TEAM_VS, MatchTeamTypes.TAG_TEAM_VS):
        need_slot_updates = True
        i = 0
        for slot in slots:
            if slot["account_id"] == -1:
                continue

            if i & 1:
                slot["team"] = MatchTeams.BLUE
            else:
                slot["team"] = MatchTeams.RED

            i += 1

    # if freemod is activated the match mods are transferred to the slots
    # if freemod is disabled the mods will clear
    if osu_match_data["freemods_enabled"] != match["freemods_enabled"]:
        # copy bancho's behaviour
        if osu_match_data["freemods_enabled"]:
            mods = match["mods"] & (~Mods.SPEED_CHANGING)
            osu_match_data["mods"] = match["mods"] & Mods.SPEED_CHANGING
        else:
            mods = Mods.NOMOD

        need_slot_updates = True
        for slot in slots:
            if slot["account_id"] != -1:
                slot["mods"] = mods

    # update slots if needed
    if need_slot_updates:
        for slot in slots:
            if slot["account_id"] != -1:
                await multiplayer_slots.partial_update(
                    match_id=match_id,
                    **slot,
                )

    match_params = {
        "match_name": osu_match_data["match_name"],
        "match_password": osu_match_data["match_password"],
        "beatmap_name": osu_match_data["beatmap_name"],
        "beatmap_id": osu_match_data["beatmap_id"],
        "beatmap_md5": osu_match_data["beatmap_md5"],
        "host_account_id": osu_match_data["host_account_id"],
        "game_mode": game_mode,
        "mods": osu_match_data["mods"],
        "win_condition": osu_match_data["win_condition"],
        "team_type": osu_match_data["team_type"],
        "freemods_enabled": osu_match_data["freemods_enabled"],
        "random_seed": osu_match_data["random_seed"],
    }

    await multiplayer_matches.partial_update(
        match_id=match_id,
        **match_params,
    )

    # inform relevant places of the new match state
    await _broadcast_match_updates(match_id)

    logger.info(
        "User changed match settings.",
        user_id=session["account_id"],
        match_id=match_id,
        **match_params,
    )


# MATCH_START = 44


@bancho_handler(packets.ClientPackets.MATCH_START)
async def match_start_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if not match_id:
        logger.warning(
            "A user attempted to start a match but they aren't in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to start a match but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    if match["host_account_id"] != session["account_id"]:
        logger.warning(
            "A user attempted to start a match but they aren't the host.",
            user_id=session["account_id"],
            match_id=match_id,
            match_host=match["host_account_id"],
        )
        return

    match = await multiplayer_matches.partial_update(
        match_id=match_id,
        status=MatchStatus.PLAYING,
    )
    assert not isinstance(match, ServiceError)

    slots = await multiplayer_slots.fetch_all(match_id)
    for i, slot in enumerate(slots):
        if slot["status"] & SlotStatus.CAN_START:
            new_slot = await multiplayer_slots.partial_update(
                match_id=match_id,
                slot_id=slot["slot_id"],
                status=SlotStatus.PLAYING,
            )
            assert new_slot
            slots[i] = new_slot

    vanilla_game_mode = game_modes.for_client(match["game_mode"])

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
        vanilla_game_mode,
        match["win_condition"],
        match["team_type"],
        match["freemods_enabled"],
        [s["mods"] for s in slots] if match["freemods_enabled"] else [],
        match["random_seed"],
    )

    match_started_packet = packets.write_match_start_packet(*packet_params)
    await _broadcast_to_match(
        match_id=match_id,
        data=match_started_packet,
        slot_flags=SlotStatus.PLAYING,
    )

    await _broadcast_to_lobby(match_started_packet)

    logger.info(
        "User started a multiplayer match.",
        user_id=session["account_id"],
        match_id=match_id,
    )


# MATCH_SCORE_UPDATE = 47


@bancho_handler(packets.ClientPackets.MATCH_SCORE_UPDATE)
async def match_score_update_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user sent a match score frame but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user sent a match score frame but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user sent a match score frame but they don't have a slot.",
            user_id=session["account_id"],
        )
        return

    new_packet_data = packet_data[:4] + chr(slot["slot_id"]).encode() + packet_data[5:]

    score_update_packet = packets.write_match_score_update_packet(new_packet_data)
    await _broadcast_to_match(
        match_id=match_id,
        data=score_update_packet,
        slot_flags=SlotStatus.PLAYING,
    )


# MATCH_COMPLETE = 49


@bancho_handler(packets.ClientPackets.MATCH_COMPLETE)
async def match_complete_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to tell us they completed but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to tell us they completed but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        status=SlotStatus.WAITING_FOR_END,
    )

    all_done = await multiplayer_slots.all_completed(match_id)
    if not all_done:
        return

    done_packet = packets.write_match_complete_packet()
    await _broadcast_to_match(
        match_id=match_id,
        data=done_packet,
        slot_flags=SlotStatus.COMPLETE,
    )

    slots = await multiplayer_slots.fetch_all(match_id)
    for slot in slots:
        if slot["status"] == SlotStatus.WAITING_FOR_END:
            await multiplayer_slots.partial_update(
                match_id=match_id,
                slot_id=slot["slot_id"],
                status=SlotStatus.NOT_READY,
                loaded=False,
                skipped=False,
            )

    await _broadcast_match_updates(match_id)

    logger.info(
        "Match has completed.",
        match_id=match_id,
    )


# MATCH_CHANGE_MODS = 51


@bancho_handler(packets.ClientPackets.MATCH_CHANGE_MODS)
async def match_change_mods_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if not match_id:
        logger.warning(
            "A user attempted to change mods but they aren't in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to change mods but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    is_host = match["host_account_id"] == session["account_id"]

    reader = packets.PacketReader(packet_data)
    mods = reader.read_i32()

    clientside_mode = game_modes.for_client(match["game_mode"])
    serverside_mode = game_modes.for_server(
        clientside_mode,
        mods,
    )

    if match["freemods_enabled"]:
        # apply the speed changing mods to the match
        if is_host:
            speed_changing_mods = mods & Mods.SPEED_CHANGING
            await multiplayer_matches.partial_update(match_id, mods=speed_changing_mods)

        # and apply the non-speed changing mods to the slot
        speedless_mods = mods & (~Mods.SPEED_CHANGING)

        slot = await multiplayer_slots.fetch_one_by_session_id(
            match_id=match_id, session_id=session["session_id"]
        )
        if not slot:
            logger.warning(
                "A user attempted to change mods but their slot doesn't exist.",
                user_id=session["account_id"],
                match_id=match_id,
            )
            return

        await multiplayer_slots.partial_update(
            match_id=match_id,
            slot_id=slot["slot_id"],
            mods=speedless_mods,
        )

        # set the sessions game mode if needed
        if presence["game_mode"] != serverside_mode:
            await sessions.partial_update(
                session_id=session["session_id"],
                presence={
                    "game_mode": serverside_mode,
                    "mods": mods,
                },
            )
    elif is_host:
        # set all sessions game mode if needed
        if match["game_mode"] != serverside_mode:
            slots = await multiplayer_slots.fetch_all(match_id)
            for slot in slots:
                if slot["account_id"] != -1:
                    await sessions.partial_update(
                        session_id=slot["session_id"],
                        presence={
                            "game_mode": serverside_mode,
                            "mods": mods,
                        },
                    )

        await multiplayer_matches.partial_update(
            match_id=match_id, game_mode=serverside_mode, mods=mods
        )
    else:
        logger.warning(
            "A user attempted to change the match mods but they aren't allowed to.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    await _broadcast_match_updates(match_id)

    logger.info(
        "User changed match mods.",
        user_id=session["account_id"],
        match_id=match_id,
        mods=mods,
    )


# MATCH_LOAD_COMPLETE = 52


@bancho_handler(packets.ClientPackets.MATCH_LOAD_COMPLETE)
async def match_load_complete_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to tell us they have loaded but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to tell us they have loaded but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        loaded=True,
    )

    all_loaded = await multiplayer_slots.all_loaded(match_id)
    if not all_loaded:
        return

    all_loaded_packet = packets.write_match_all_players_loaded_packet()
    await _broadcast_to_match(
        match_id=match_id,
        data=all_loaded_packet,
        slot_flags=SlotStatus.PLAYING,
    )


# MATCH_NO_BEATMAP = 54


@bancho_handler(packets.ClientPackets.MATCH_NO_BEATMAP)
async def match_no_beatmap_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to tell us they don't have the map but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to tell us they don't have the map but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    if slot["status"] != SlotStatus.NOT_READY:
        logger.warning(
            "A user attempted to tell us they don't have the map but they are not allowed to.",
            user_id=session["account_id"],
            match_id=match_id,
            slot_id=slot["slot_id"],
            slot_status=slot["status"],
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        status=SlotStatus.NO_BEATMAP,
    )

    await _broadcast_match_updates(match_id)


# MATCH_NOT_READY = 55


@bancho_handler(packets.ClientPackets.MATCH_NOT_READY)
async def match_not_ready_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to unready but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to unready but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    if slot["status"] != SlotStatus.READY:
        logger.warning(
            "A user attempted to unready but they are not allowed to.",
            user_id=session["account_id"],
            match_id=match_id,
            slot_id=slot["slot_id"],
            slot_status=slot["status"],
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        status=SlotStatus.NOT_READY,
    )

    await _broadcast_match_updates(match_id)


# MATCH_FAILED = 56


@bancho_handler(packets.ClientPackets.MATCH_FAILED)
async def match_failed_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to fail in a match but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id,
        session_id=session["session_id"],
    )
    if not slot:
        logger.warning(
            "A user attempted to fail in a match but they don't have a slot.",
            user_id=session["account_id"],
        )
        return

    player_failed_packet = packets.write_match_player_failed_packet(slot["slot_id"])
    await _broadcast_to_match(
        match_id=match_id,
        data=player_failed_packet,
        slot_flags=SlotStatus.PLAYING,
    )


# MATCH_HAS_BEATMAP = 59


@bancho_handler(packets.ClientPackets.MATCH_HAS_BEATMAP)
async def match_has_beatmap_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to tell us they have the map but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to tell us they have the map but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    if slot["status"] != SlotStatus.NO_BEATMAP:
        logger.warning(
            "A user attempted to tell us they have the map but they are not allowed to.",
            user_id=session["account_id"],
            match_id=match_id,
            slot_id=slot["slot_id"],
            slot_status=slot["status"],
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        status=SlotStatus.NOT_READY,
    )

    await _broadcast_match_updates(match_id)


# MATCH_SKIP_REQUEST = 60


@bancho_handler(packets.ClientPackets.MATCH_SKIP_REQUEST)
async def match_skip_request(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to skip but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id, session_id=session["session_id"]
    )
    if not slot:
        logger.warning(
            "A user attempted to skip but they don't have a slot.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        skipped=True,
    )

    skip_packet = packets.write_match_player_skipped_packet(slot["slot_id"])

    all_skipped = await multiplayer_slots.all_skipped(match_id)
    if all_skipped:
        skip_packet += packets.write_match_skip_packet()

    await _broadcast_to_match(
        match_id=match_id,
        data=skip_packet,
        slot_flags=SlotStatus.PLAYING,
    )


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
# NOTE: this is deprecated and not used lol


# MATCH_TRANSFER_HOST = 70


@bancho_handler(packets.ClientPackets.MATCH_TRANSFER_HOST)
async def match_transfer_host_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if match_id is None:
        logger.warning(
            "A user attempted to change hosts but they are not in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to change hosts but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    # only the host can transfer the host
    if match["host_account_id"] != session["account_id"]:
        logger.warning(
            "A user attempted to change hosts but they are not the host.",
            user_id=session["account_id"],
            match_id=match_id,
            match_host=match["host_account_id"],
        )
        return

    reader = packets.PacketReader(packet_data)
    slot_id = reader.read_i32()

    slot = await multiplayer_slots.fetch_one(match_id, slot_id)
    if not slot:
        logger.warning(
            "A user attempted to change hosts but the slot doesn't exist.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    new_host_id = slot["account_id"]
    if new_host_id == -1:
        logger.warning(
            "A user attempted to change hosts but the slot doesn't have a user.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    await multiplayer_matches.partial_update(
        match_id=match_id, host_account_id=new_host_id
    )

    await _broadcast_match_updates(match_id)


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


@bancho_handler(packets.ClientPackets.MATCH_CHANGE_TEAM)
async def match_change_team_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if not match_id:
        logger.warning(
            "A user attempted to change teams but isn't in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to change teams but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    if match["team_type"] not in (MatchTeamTypes.TEAM_VS, MatchTeamTypes.TAG_TEAM_VS):
        logger.warning(
            "A user attempted to change teams but the match is not in versus mode.",
            user_id=session["account_id"],
            match_id=match_id,
            match_team_type=match["team_type"],
        )
        return

    slot = await multiplayer_slots.fetch_one_by_session_id(
        match_id=match_id,
        session_id=session["session_id"],
    )
    if not slot:
        logger.warning(
            "A user attempted to change teams but their slot doesn't exist.",
            user_id=session["account_id"],
            match_id=match_id,
        )
        return

    if slot["team"] == MatchTeams.BLUE:
        new_team = MatchTeams.RED
    else:
        new_team = MatchTeams.BLUE

    await multiplayer_slots.partial_update(
        match_id=match_id,
        slot_id=slot["slot_id"],
        team=new_team,
    )

    await _broadcast_match_updates(match_id)

    logger.info(
        "User changed match teams.",
        user_id=session["account_id"],
        match_id=match_id,
        slot_team=new_team,
    )


# CHANNEL_PART = 78


@bancho_handler(packets.ClientPackets.CHANNEL_PART)
async def user_leaves_channel_handler(session: "Session", packet_data: bytes):
    packet_reader = packets.PacketReader(packet_data)
    channel_name = packet_reader.read_string()

    channel = await channels.fetch_one_by_name(channel_name)
    if channel is None:
        return

    # NOTE: we ignore #lobby to enqueue the match updates
    # and we actually remove them from the channel on lobby part
    presence = session["presence"]
    if channel["name"] == "#lobby" and presence["receive_match_updates"]:
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

    for other_session in await sessions.fetch_all(
        has_any_privilege_bit=channel["read_privileges"]
    ):
        await packet_bundles.enqueue(
            other_session["session_id"],
            packets.write_channel_info_packet(
                channel["name"],
                channel["topic"],
                len(current_channel_members) - 1
                if len(current_channel_members) > 0
                else 0,
            ),
        )


# RECEIVE_UPDATES = 79


# SET_AWAY_MESSAGE = 82


@bancho_handler(packets.ClientPackets.SET_AWAY_MESSAGE)
async def set_away_message_handler(session: "Session", packet_data: bytes) -> None:
    reader = packets.PacketReader(packet_data)

    away_osu_message = reader.read_osu_message()

    if away_osu_message["message_content"] != "":
        away_message = away_osu_message["message_content"]

        if len(away_message) > 500:
            await packet_bundles.enqueue(
                session["session_id"],
                packets.write_notification_packet(
                    f"Please keep away messages to under 500 characters."
                ),
            )
            return

    else:
        away_message = None

    maybe_session = await sessions.partial_update(
        session["session_id"],
        presence={"away_message": away_message},
    )
    assert maybe_session is not None
    session = maybe_session

    if away_message is None:
        notification_content = "Your away message has been cleared."
    else:
        notification_content = (
            f"Your away message has been updated to:\n\n{away_message}"
        )

    await packet_bundles.enqueue(
        session["session_id"], packets.write_notification_packet(notification_content)
    )


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

        vanilla_game_mode = game_modes.for_client(
            other_session["presence"]["game_mode"]
        )

        other_global_rank = await ranking.get_global_rank(
            other_stats["account_id"],
            other_stats["game_mode"],
        )
        await packet_bundles.enqueue(
            session["session_id"],
            data=packets.write_user_stats_packet(
                other_stats["account_id"],
                other_session["presence"]["action"],
                other_session["presence"]["info_text"],
                other_session["presence"]["beatmap_md5"],
                other_session["presence"]["mods"],
                vanilla_game_mode,
                other_session["presence"]["beatmap_id"],
                other_stats["ranked_score"],
                other_stats["accuracy"],
                other_stats["play_count"],
                other_stats["total_score"],
                other_global_rank,
                other_stats["performance_points"],
            ),
        )


# MATCH_INVITE = 87


@bancho_handler(packets.ClientPackets.MATCH_INVITE)
async def match_invite_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if not match_id:
        logger.warning(
            "A user attempted to invite someone to a match but isn't in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to invite someone to a match but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    reader = packets.PacketReader(packet_data)
    target_id = reader.read_i32()

    target_session = await sessions.fetch_by_account_id(target_id)
    if not target_session:
        logger.warning(
            "A user attempted to invite someone to a match who is offline.",
            user_id=session["account_id"],
        )
        return

    invite_msg = (
        "Come join my multiplayer match!\n"
        f"[osump://{match_id}/{match['match_password']} {match['match_name']}]"
    )

    invite_msg_packet = packets.write_send_message_packet(
        sender_name=presence["username"],
        message_content=invite_msg,
        recipient_name=target_session["presence"]["username"],
        sender_id=session["account_id"],
    )

    await packet_bundles.enqueue(
        session_id=target_session["session_id"],
        data=invite_msg_packet,
    )

    logger.info(
        "User has invited another user to a match.",
        user_id=session["account_id"],
        target_user_id=target_session["account_id"],
        match_id=match_id,
    )


# MATCH_CHANGE_PASSWORD = 90


@bancho_handler(packets.ClientPackets.MATCH_CHANGE_PASSWORD)
async def match_change_password_handler(session: "Session", packet_data: bytes):
    presence = session["presence"]
    match_id = presence["multiplayer_match_id"]
    if not match_id:
        logger.warning(
            "A user attempted to change the match password but isn't in a match.",
            user_id=session["account_id"],
        )
        return

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "A user attempted to change the match password but their match doesn't exist.",
            user_id=session["account_id"],
        )
        return

    if match["host_account_id"] != session["account_id"]:
        logger.warning(
            "A user attempted to change the match password but they aren't the host.",
            user_id=session["account_id"],
            match_id=match_id,
            match_host=match["host_account_id"],
        )
        return

    reader = packets.PacketReader(packet_data)
    osu_match_data = reader.read_osu_match()

    await multiplayer_matches.partial_update(
        match_id=match_id,
        match_password=osu_match_data["match_password"],
    )

    await _broadcast_match_updates(
        match_id=match_id,
        send_to_lobby=False,
    )

    logger.info(
        "User updated the match password.",
        user_id=session["account_id"],
        match_id=match_id,
    )


# TOURNAMENT_MATCH_INFO_REQUEST = 93


# USER_PRESENCE_REQUEST = 97


# USER_PRESENCE_REQUEST_ALL = 98


# TOGGLE_BLOCK_NON_FRIEND_DMS = 99


# TOURNAMENT_JOIN_MATCH_CHANNEL = 108


# TOURNAMENT_LEAVE_MATCH_CHANNEL = 109
