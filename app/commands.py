import random
from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

from app import game_modes
from app import logger
from app import packets
from app.errors import ServiceError
from app.privileges import ServerPrivileges
from app.ranked_statuses import BeatmapRankedStatus
from app.repositories import accounts
from app.repositories import channel_members
from app.repositories import channels
from app.repositories import multiplayer_slots
from app.repositories import packet_bundles
from app.repositories import relationships
from app.repositories.multiplayer_matches import MatchStatus
from app.repositories.multiplayer_slots import SlotStatus
from app.services import beatmaps
from app.services import multiplayer_matches
from app.services import multiplayer_matches as mp_matches
from app.services import beatmaps
from app import game_modes

if TYPE_CHECKING:
    from app.repositories.sessions import Session

# TODO: create the concept of an "application", where developers can
# register to have their own bots running on the server, which can
# act via interactions with our rest api. re-implement this with that.

CommandHandler = Callable[["Session", list[str]], Awaitable[str | None]]


class Command:
    def __init__(
        self,
        trigger: str,
        callback: CommandHandler,
        privileges: int | None = None,
    ) -> None:
        self.trigger = trigger
        self.privileges = privileges
        self.callback = callback


commands: dict[str, Command] = {}


def get_command(trigger: str) -> Command | None:
    return commands.get(trigger)


def command(
    trigger: str,
    privileges: int | None = None,
) -> Callable[[CommandHandler], CommandHandler]:
    def wrapper(callback: CommandHandler) -> CommandHandler:
        command = Command(trigger, callback, privileges)
        commands[trigger] = command
        return callback

    return wrapper


class CommandSet:
    def __init__(
        self,
        trigger: str,
        documentation: str,
    ) -> None:
        self.trigger = trigger
        self.documentation = documentation
        self.subcommands: dict[str, Command] = {}

    def command(
        self,
        trigger: str,
        privileges: int | None = None,
    ) -> Callable[[CommandHandler], CommandHandler]:
        trigger = trigger.removeprefix(f"{self.trigger} ")

        def wrapper(callback: CommandHandler) -> CommandHandler:
            command = Command(trigger, callback, privileges)
            self.subcommands[trigger] = command
            return callback

        return wrapper

    def get_command(self, trigger: str) -> Command | None:
        return self.subcommands.get(trigger)


command_sets: dict[str, CommandSet] = {}


def get_command_set(trigger: str) -> CommandSet | None:
    return command_sets.get(trigger)


@command("!help")
async def help_handler(session: "Session", args: list[str]) -> str | None:
    """Display this help message."""
    response_lines = []

    # add regular commands
    for trigger, command in commands.items():
        # don't show commands without documentation
        documentation = command.callback.__doc__
        if not documentation:
            continue

        # don't show commands that the user can't access
        if command.privileges is not None:
            if (session["presence"]["privileges"] & command.privileges) == 0:
                continue

        response_lines.append(f"* {trigger} - {documentation}")

    if command_sets:
        response_lines.append("")  # \n

    # add command sets
    for trigger, command_set in command_sets.items():
        documentation = command_set.documentation

        response_lines.append(f"[ {trigger} ] - {documentation}")

        for trigger, command in command_set.subcommands.items():
            # don't show commands without documentation
            documentation = command.callback.__doc__
            if not documentation:
                continue

            # don't show commands that the user can't access
            if command.privileges is not None:
                if (session["presence"]["privileges"] & command.privileges) == 0:
                    continue

            response_lines.append(f"* {trigger} - {documentation}")

            # TODO: \n between sets?

    return "\n".join(response_lines)


@command("!roll")
async def roll_handler(session: "Session", args: list[str]) -> str | None:
    """Roll a random number between 0 and a given number."""
    random_number_max = int(args[0]) if args else 100
    return str(random.randrange(0, random_number_max))


@command("!block")
async def block_handler(session: "Session", args: list[str]) -> str | None:
    """Block communications with another user."""
    own_presence = session["presence"]

    account_to_be_blocked = await accounts.fetch_by_username(args[0])
    if account_to_be_blocked is None:
        return f"{args[0]} could not be blocked"

    all_relationships = await relationships.fetch_all(session["account_id"])

    for relationship in all_relationships:
        if relationship["target_id"] == account_to_be_blocked["account_id"]:
            return f"{args[0]} is already blocked"

    await relationships.create(
        account_id=session["account_id"],
        target_id=account_to_be_blocked["account_id"],
        relationship="blocked",
    )

    return f"{own_presence['username']} successfully blocked {args[0]}"


async def _shared_base_for_edit_map_handlers(
    last_np_beatmap_id: int | None,
    ranked_status: int,
) -> str | None:
    if last_np_beatmap_id is None:
        return "You must first use /np to send a beatmap"

    beatmap = await beatmaps.fetch_one(beatmap_id=last_np_beatmap_id)
    if isinstance(beatmap, ServiceError):
        if beatmap is ServiceError.BEATMAPS_NOT_FOUND:
            return "Beatmap not found."

        logger.error(
            "An error occurred while fetching a beatmap.",
            beatmap_id=last_np_beatmap_id,
        )
        return "An error occurred while fetching the beatmap."

    beatmap = await beatmaps.partial_update(
        last_np_beatmap_id,
        ranked_status=ranked_status,
        ranked_status_manually_changed=True,
    )
    if isinstance(beatmap, ServiceError):
        if beatmap is ServiceError.BEATMAPS_NOT_FOUND:
            return "Beatmap not found."

        logger.error(
            "An error occurred while updating a beatmap.",
            beatmap_id=last_np_beatmap_id,
            ranked_status=ranked_status,
        )
        return "An error occurred while updating the beatmap."

    status_change_verb = {
        BeatmapRankedStatus.PENDING: "unranked",
        BeatmapRankedStatus.RANKED: "ranked",
        BeatmapRankedStatus.APPROVED: "approved",
        BeatmapRankedStatus.QUALIFIED: "qualified",
        BeatmapRankedStatus.LOVED: "loved",
    }[ranked_status]

    # TODO: post to #announce

    return f"Beatmap successfully {status_change_verb}"


@command("!rank", privileges=ServerPrivileges.BEATMAP_NOMINATOR)
async def rank_handler(session: "Session", args: list[str]) -> str | None:
    """Rank the previously /np'ed beatmap."""
    return await _shared_base_for_edit_map_handlers(
        session["presence"]["last_np_beatmap_id"],
        BeatmapRankedStatus.RANKED,
    )


@command("!love", privileges=ServerPrivileges.BEATMAP_NOMINATOR)
async def love_handler(session: "Session", args: list[str]) -> str | None:
    """Love the previously /np'ed beatmap."""
    return await _shared_base_for_edit_map_handlers(
        session["presence"]["last_np_beatmap_id"],
        BeatmapRankedStatus.LOVED,
    )


@command("!unrank", privileges=ServerPrivileges.BEATMAP_NOMINATOR)
async def unrank_handler(session: "Session", args: list[str]) -> str | None:
    """Unrank the previously /np'ed beatmap."""
    return await _shared_base_for_edit_map_handlers(
        session["presence"]["last_np_beatmap_id"],
        BeatmapRankedStatus.PENDING,
    )


# TODO: qualify & approve commands?

multiplayer_commands = CommandSet("!mp", documentation="Multiplayer commands")
command_sets[multiplayer_commands.trigger] = multiplayer_commands


@multiplayer_commands.command("!mp start")
async def match_start_handler(session: "Session", args: list[str]) -> str | None:
    """Start a multiplayer match."""
    match_id = session["presence"]["multiplayer_match_id"]
    if match_id is None:
        return "These commands only have a function in a multiplayer match"

    match = await multiplayer_matches.fetch_one(match_id)
    if isinstance(match, ServiceError):
        logger.warning(
            "Failed to fetch a multiplayer match",
            match_id=match_id,
            username=session["presence"]["username"],
            account_id=session["account_id"],
        )
        return

    if (
        session["account_id"] != match["host_account_id"]
        and not session["presence"]["privileges"] & ServerPrivileges.MULTIPLAYER_STAFF
    ):
        return "You are not the host of this match"

    match = await multiplayer_matches.partial_update(
        match["match_id"],
        status=MatchStatus.PLAYING,
    )
    assert not isinstance(match, ServiceError)

    slots = await multiplayer_slots.fetch_all(match["match_id"])
    for i, slot in enumerate(slots):
        if slot["status"] & SlotStatus.CAN_START:
            new_slot = await multiplayer_slots.partial_update(
                match["match_id"],
                slot_id=slot["slot_id"],
                status=SlotStatus.PLAYING,
            )
            assert new_slot
            slots[i] = new_slot

    vanilla_game_mode = game_modes.for_client(match["game_mode"])

    osu_match_data: packets.OsuMatch = {
        "match_id": match["match_id"],
        "match_in_progress": match["status"] == MatchStatus.PLAYING,
        "mods": match["mods"],
        "match_name": match["match_name"],
        "match_password": match["match_password"],
        "beatmap_name": match["beatmap_name"],
        "beatmap_id": match["beatmap_id"],
        "beatmap_md5": match["beatmap_md5"],
        "slot_statuses": [s["status"] for s in slots],
        "slot_teams": [s["team"] for s in slots],
        "per_slot_account_ids": [
            s["account_id"] for s in slots if s["status"] & SlotStatus.HAS_PLAYER != 0
        ],
        "host_account_id": match["host_account_id"],
        "game_mode": vanilla_game_mode,
        "win_condition": match["win_condition"],
        "team_type": match["team_type"],
        "freemods_enabled": match["freemods_enabled"],
        "per_slot_mods": [s["mods"] for s in slots]
        if match["freemods_enabled"]
        else [],
        "random_seed": match["random_seed"],
    }

    match_started_packet = packets.write_match_start_packet(
        osu_match_data,
        should_send_password=False,
    )

    for slot in slots:
        if slot["account_id"] == -1 or (slot["status"] & SlotStatus.PLAYING) == 0:
            continue

        await packet_bundles.enqueue(
            slot["session_id"],
            data=match_started_packet,
        )

    lobby_channel = await channels.fetch_one_by_name("#lobby")
    if lobby_channel is None:
        logger.error("Failed to fetch #lobby channel")
        return

    for session_id in await channel_members.members(lobby_channel["channel_id"]):
        await packet_bundles.enqueue(
            session_id,
            data=match_started_packet,
        )


@multiplayer_commands.command("!mp map")
async def multiplayer_map_handler(session: "Session", args: list[str]) -> str | None:
    match_id = session["presence"]["multiplayer_match_id"]
    if match_id is None:
        return "Invalid match ID!"

    if len(args) < 1:
        print("Please provide a beatmap ID!")
        return

    beatmap_id = int(args[0])
    beatmap = await beatmaps.fetch_one(
        beatmap_id=beatmap_id,
    )

    if isinstance(beatmap, ServiceError):
        return "Beatmap not found!"

    match = await mp_matches.partial_update(
        match_id=match_id,
        beatmap_id=beatmap_id,
    )

    assert not isinstance(match, ServiceError)

    return beatmaps.create_beatmap_chat_embed(
        beatmap_set_id=beatmap["beatmap_set_id"],
        beatmap_id=beatmap["beatmap_id"],
        artist=beatmap["artist"],
        title=beatmap["title"],
        version=beatmap["version"],
        creator=beatmap["creator"],
        mode_string=game_modes.to_string(beatmap["mode"]),
    )
