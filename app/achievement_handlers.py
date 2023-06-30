from collections.abc import Awaitable
from collections.abc import Callable
from enum import IntEnum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.repositories.osu_sessions import OsuSession
    from app.repositories.beatmaps import Beatmap
    from app.repositories.scores import Score

AchievementHandler = Callable[["OsuSession", "Beatmap", "Score"], Awaitable[bool]]

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
    OSU_PASS_1_STAR = 1
    OSU_PASS_2_STAR = 2
    OSU_PASS_3_STAR = 3
    OSU_PASS_4_STAR = 4
    OSU_PASS_5_STAR = 5
    OSU_PASS_6_STAR = 6
    OSU_PASS_7_STAR = 7
    OSU_PASS_8_STAR = 8
    OSU_PASS_9_STAR = 9
    OSU_PASS_10_STAR = 10
    OSU_FULL_COMBO_1_STAR = 11
    OSU_FULL_COMBO_2_STAR = 12
    OSU_FULL_COMBO_3_STAR = 13
    OSU_FULL_COMBO_4_STAR = 14
    OSU_FULL_COMBO_5_STAR = 15
    OSU_FULL_COMBO_6_STAR = 16
    OSU_FULL_COMBO_7_STAR = 17
    OSU_FULL_COMBO_8_STAR = 18
    OSU_FULL_COMBO_9_STAR = 19
    OSU_FULL_COMBO_10_STAR = 20
    OSU_COMBO_500 = 21
    OSU_COMBO_750 = 22
    OSU_COMBO_1000 = 23
    OSU_COMBO_2000 = 24
    TAIKO_PASS_1_STAR = 25
    TAIKO_PASS_2_STAR = 26
    TAIKO_PASS_3_STAR = 27
    TAIKO_PASS_4_STAR = 28
    TAIKO_PASS_5_STAR = 29
    TAIKO_PASS_6_STAR = 30
    TAIKO_PASS_7_STAR = 31
    TAIKO_PASS_8_STAR = 32
    TAIKO_FULL_COMBO_1_STAR = 33
    TAIKO_FULL_COMBO_2_STAR = 34
    TAIKO_FULL_COMBO_3_STAR = 35
    TAIKO_FULL_COMBO_4_STAR = 36
    TAIKO_FULL_COMBO_5_STAR = 37
    TAIKO_FULL_COMBO_6_STAR = 38
    TAIKO_FULL_COMBO_7_STAR = 39
    TAIKO_FULL_COMBO_8_STAR = 40
    CTB_PASS_1_STAR = 41
    CTB_PASS_2_STAR = 42
    CTB_PASS_3_STAR = 43
    CTB_PASS_4_STAR = 44
    CTB_PASS_5_STAR = 45
    CTB_PASS_6_STAR = 46
    CTB_PASS_7_STAR = 47
    CTB_PASS_8_STAR = 48
    CTB_FULL_COMBO_1_STAR = 49
    CTB_FULL_COMBO_2_STAR = 50
    CTB_FULL_COMBO_3_STAR = 51
    CTB_FULL_COMBO_4_STAR = 52
    CTB_FULL_COMBO_5_STAR = 53
    CTB_FULL_COMBO_6_STAR = 54
    CTB_FULL_COMBO_7_STAR = 55
    CTB_FULL_COMBO_8_STAR = 56
    MANIA_PASS_1_STAR = 57
    MANIA_PASS_2_STAR = 58
    MANIA_PASS_3_STAR = 59
    MANIA_PASS_4_STAR = 60
    MANIA_PASS_5_STAR = 61
    MANIA_PASS_6_STAR = 62
    MANIA_PASS_7_STAR = 63
    MANIA_PASS_8_STAR = 64
    MANIA_FULL_COMBO_1_STAR = 65
    MANIA_FULL_COMBO_2_STAR = 66
    MANIA_FULL_COMBO_3_STAR = 67
    MANIA_FULL_COMBO_4_STAR = 68
    MANIA_FULL_COMBO_5_STAR = 69
    MANIA_FULL_COMBO_6_STAR = 70
    MANIA_FULL_COMBO_7_STAR = 71
    MANIA_FULL_COMBO_8_STAR = 72
    ALL_INTRO_SUDDENDEATH = 73
    ALL_INTRO_HIDDEN = 74
    ALL_INTRO_PERFECT = 75
    ALL_INTRO_HARDROCK = 76
    ALL_INTRO_DOUBLETIME = 77
    ALL_INTRO_FLASHLIGHT = 78
    ALL_INTRO_EASY = 79
    ALL_INTRO_NOFAIL = 80
    ALL_INTRO_NIGHT_CORE = 81
    ALL_INTRO_HALFTIME = 82
    ALL_INTRO_SPUNOUT = 83


# TODO: separate achievements for vanilla, relax and autopilot


@achievement_handler(Achievement.OSU_PASS_1_STAR)
async def osu_pass_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_2_STAR)
async def osu_pass_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_3_STAR)
async def osu_pass_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_4_STAR)
async def osu_pass_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_5_STAR)
async def osu_pass_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_6_STAR)
async def osu_pass_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_7_STAR)
async def osu_pass_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_8_STAR)
async def osu_pass_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_9_STAR)
async def osu_pass_9_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 9 <= beatmap["star_rating"] < 10
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_PASS_10_STAR)
async def osu_pass_10_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 10 <= beatmap["star_rating"] < 11
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_1_STAR)
async def osu_full_combo_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_2_STAR)
async def osu_full_combo_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_3_STAR)
async def osu_full_combo_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_4_STAR)
async def osu_full_combo_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_5_STAR)
async def osu_full_combo_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_6_STAR)
async def osu_full_combo_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_7_STAR)
async def osu_full_combo_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_8_STAR)
async def osu_full_combo_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_9_STAR)
async def osu_full_combo_9_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 9 <= beatmap["star_rating"] < 10
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_FULL_COMBO_10_STAR)
async def osu_full_combo_10_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 10 <= beatmap["star_rating"] < 11
        and score["game_mode"] == 0
    )


@achievement_handler(Achievement.OSU_COMBO_500)
async def osu_combo_500(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return 500 <= score["highest_combo"] < 750 and score["game_mode"] == 0


@achievement_handler(Achievement.OSU_COMBO_750)
async def osu_combo_750(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return 750 <= score["highest_combo"] < 1000 and score["game_mode"] == 0


@achievement_handler(Achievement.OSU_COMBO_1000)
async def osu_combo_1000(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return 1000 <= score["highest_combo"] < 2000 and score["game_mode"] == 0


@achievement_handler(Achievement.OSU_COMBO_2000)
async def osu_combo_2000(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return 2000 <= score["highest_combo"] and score["game_mode"] == 0


@achievement_handler(Achievement.TAIKO_PASS_1_STAR)
async def taiko_pass_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_2_STAR)
async def taiko_pass_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_3_STAR)
async def taiko_pass_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_4_STAR)
async def taiko_pass_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_5_STAR)
async def taiko_pass_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_6_STAR)
async def taiko_pass_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_7_STAR)
async def taiko_pass_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_PASS_8_STAR)
async def taiko_pass_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_1_STAR)
async def taiko_full_combo_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_2_STAR)
async def taiko_full_combo_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_3_STAR)
async def taiko_full_combo_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_4_STAR)
async def taiko_full_combo_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_5_STAR)
async def taiko_full_combo_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_6_STAR)
async def taiko_full_combo_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_7_STAR)
async def taiko_full_combo_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.TAIKO_FULL_COMBO_8_STAR)
async def taiko_full_combo_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 1
    )


@achievement_handler(Achievement.CTB_PASS_1_STAR)
async def ctb_pass_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_2_STAR)
async def ctb_pass_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_3_STAR)
async def ctb_pass_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_4_STAR)
async def ctb_pass_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_5_STAR)
async def ctb_pass_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_6_STAR)
async def ctb_pass_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_7_STAR)
async def ctb_pass_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_PASS_8_STAR)
async def ctb_pass_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_1_STAR)
async def ctb_full_combo_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_2_STAR)
async def ctb_full_combo_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_3_STAR)
async def ctb_full_combo_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_4_STAR)
async def ctb_full_combo_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_5_STAR)
async def ctb_full_combo_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_6_STAR)
async def ctb_full_combo_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_7_STAR)
async def ctb_full_combo_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.CTB_FULL_COMBO_8_STAR)
async def ctb_full_combo_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 2
    )


@achievement_handler(Achievement.MANIA_PASS_1_STAR)
async def mania_pass_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_2_STAR)
async def mania_pass_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_3_STAR)
async def mania_pass_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_4_STAR)
async def mania_pass_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_5_STAR)
async def mania_pass_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_6_STAR)
async def mania_pass_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_7_STAR)
async def mania_pass_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_PASS_8_STAR)
async def mania_pass_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        (score["mods"] & 1 == 0)
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_1_STAR)
async def mania_full_combo_1_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 1 <= beatmap["star_rating"] < 2
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_2_STAR)
async def mania_full_combo_2_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 2 <= beatmap["star_rating"] < 3
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_3_STAR)
async def mania_full_combo_3_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 3 <= beatmap["star_rating"] < 4
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_4_STAR)
async def mania_full_combo_4_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 4 <= beatmap["star_rating"] < 5
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_5_STAR)
async def mania_full_combo_5_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 5 <= beatmap["star_rating"] < 6
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_6_STAR)
async def mania_full_combo_6_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 6 <= beatmap["star_rating"] < 7
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_7_STAR)
async def mania_full_combo_7_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 7 <= beatmap["star_rating"] < 8
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.MANIA_FULL_COMBO_8_STAR)
async def mania_full_combo_8_star(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return (
        score["full_combo"]
        and 8 <= beatmap["star_rating"] < 9
        and score["game_mode"] == 3
    )


@achievement_handler(Achievement.ALL_INTRO_SUDDENDEATH)
async def all_intro_suddendeath(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] == 32  # TODO: why is this inconsistent?


@achievement_handler(Achievement.ALL_INTRO_HIDDEN)
async def all_intro_hidden(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 8 == 8


@achievement_handler(Achievement.ALL_INTRO_PERFECT)
async def all_intro_perfect(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 16384 == 16384


@achievement_handler(Achievement.ALL_INTRO_HARDROCK)
async def all_intro_hardrock(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 16 == 16


@achievement_handler(Achievement.ALL_INTRO_DOUBLETIME)
async def all_intro_doubletime(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 64 == 64


@achievement_handler(Achievement.ALL_INTRO_FLASHLIGHT)
async def all_intro_flashlight(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 1024 == 1024


@achievement_handler(Achievement.ALL_INTRO_EASY)
async def all_intro_easy(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 2 == 2


@achievement_handler(Achievement.ALL_INTRO_NOFAIL)
async def all_intro_nofail(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 1 == 1


@achievement_handler(Achievement.ALL_INTRO_NIGHT_CORE)
async def all_intro_night_core(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 512 == 512


@achievement_handler(Achievement.ALL_INTRO_HALFTIME)
async def all_intro_halftime(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 256 == 256


@achievement_handler(Achievement.ALL_INTRO_SPUNOUT)
async def all_intro_spunout(
    osu_session: "OsuSession",
    beatmap: "Beatmap",
    score: "Score",
) -> bool:
    return score["mods"] & 4096 == 4096
