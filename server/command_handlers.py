import random
from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

from server.repositories import accounts
from server.repositories import relationships

if TYPE_CHECKING:
    from server.repositories.sessions import Session

CommandHandler = Callable[["Session", list[str]], Awaitable[str | None]]

command_handlers: dict[str, CommandHandler] = {}


def get_command_handler(trigger: str) -> CommandHandler | None:
    return command_handlers.get(trigger)


def command_handler(trigger: str) -> Callable[[CommandHandler], CommandHandler]:
    def wrapper(f: CommandHandler) -> CommandHandler:
        command_handlers[trigger] = f
        return f

    return wrapper


@command_handler("!echo")
async def echo_handler(session: "Session", args: list[str]) -> str | None:
    return " ".join(args)


@command_handler("!roll")
async def roll_handler(session: "Session", args: list[str]) -> str | None:
    random_number_max = int(args[0])
    return str(random.randrange(0, random_number_max))


@command_handler("!py")
async def py_handler(session: "Session", args: list[str]) -> str | None:
    try:
        namespace = {}
        exec("async def f():\n " + " ".join(args), namespace)
        return str(await namespace["f"]())
    except Exception as exc:
        return str(exc)


@command_handler("!block")
async def block_handler(session: "Session", args: list[str]) -> str | None:
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
