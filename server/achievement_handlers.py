from collections.abc import Awaitable
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from server.repositories.sessions import Session
    from server.repositories.beatmaps import Beatmap
    from server.repositories.scores import Score

AchievementHandler = Callable[["Session", "Beatmap", "Score"], Awaitable[bool]]

achievement_handlers: dict[int, AchievementHandler] = {}


def get_achievement_handler(achievement_id: int) -> AchievementHandler | None:
    return achievement_handlers.get(achievement_id)


def achievement_handler(
    achievement_id: int,
) -> Callable[[AchievementHandler], AchievementHandler]:
    def wrapper(f: AchievementHandler) -> AchievementHandler:
        achievement_handlers[achievement_id] = f
        return f

    return wrapper


class Achievement(IntEnum):
    ONE_STAR_FC = 1


@achievement_handler(Achievement.ONE_STAR_FC)
async def one_star_fc(
    session: "Session",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["full_combo"] and beatmap["star_rating"] == 1
