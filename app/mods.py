class Mods:
    NOMOD = 0
    NOFAIL = 1 << 0
    EASY = 1 << 1
    TOUCHSCREEN = 1 << 2  # old: 'NOVIDEO'
    HIDDEN = 1 << 3
    HARDROCK = 1 << 4
    SUDDENDEATH = 1 << 5
    DOUBLETIME = 1 << 6
    RELAX = 1 << 7
    HALFTIME = 1 << 8
    NIGHTCORE = 1 << 9
    FLASHLIGHT = 1 << 10
    AUTOPLAY = 1 << 11
    SPUNOUT = 1 << 12
    AUTOPILOT = 1 << 13
    PERFECT = 1 << 14
    KEY4 = 1 << 15
    KEY5 = 1 << 16
    KEY6 = 1 << 17
    KEY7 = 1 << 18
    KEY8 = 1 << 19
    FADEIN = 1 << 20
    RANDOM = 1 << 21
    CINEMA = 1 << 22
    TARGET = 1 << 23
    KEY9 = 1 << 24
    KEYCOOP = 1 << 25
    KEY1 = 1 << 26
    KEY3 = 1 << 27
    KEY2 = 1 << 28
    SCOREV2 = 1 << 29
    MIRROR = 1 << 30

    SPEED_CHANGING = DOUBLETIME | NIGHTCORE | HALFTIME


# TODO: to_string


def filter_invalid_mod_combinations(
    mods: int,
    vanilla_game_mode: int,
) -> int:
    """Filter out invalid mod combinations."""

    # bancho.py reference:
    # https://github.com/osuAkatsuki/bancho.py/blob/36dc2313ad8d7f62e605519bed7c218d9beae24f/app/constants/mods.py#L65-L126

    if (
        # client is attempting to switch to an invalid game mode for relax
        vanilla_game_mode == 3  # vn mania
        and mods & Mods.RELAX
    ):
        # remove relax from the mods
        mods &= ~Mods.RELAX
    elif (
        # client is attempting to switch to an invalid game mode for autopilot
        vanilla_game_mode
        in (
            1,  # taiko
            2,  # catch
            3,  # mania
        )
        and mods & Mods.AUTOPILOT
    ):
        # remove autopilot from the mods
        mods &= ~Mods.AUTOPILOT

    return mods
