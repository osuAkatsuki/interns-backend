import random
from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

from app import logger
from app.errors import ServiceError
from app.privileges import ServerPrivileges
from app.ranked_statuses import BeatmapRankedStatus
from app.repositories import accounts
from app.repositories import relationships
from app.services import beatmaps

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
        commands[trigger] = Command(trigger, callback, privileges)
        return callback

    return wrapper


@command("!help")
async def help_handler(session: "Session", args: list[str]) -> str | None:
    """Display this help message."""
    response_lines = []
    for trigger, command in commands.items():
        # don't show commands without documentation
        documentation = command.callback.__doc__
        if not documentation:
            continue

        # don't show commands that the user can't access
        if command.privileges is not None:
            if (session["presence"]["privileges"] & command.privileges) == 0:
                continue

        response_lines.append(f"{trigger} - {documentation}")

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
