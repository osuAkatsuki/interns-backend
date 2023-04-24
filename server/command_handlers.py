from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

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
