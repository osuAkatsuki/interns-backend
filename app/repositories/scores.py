from datetime import datetime
from typing import cast
from typing import Literal
from typing import TypedDict

from app import clients

READ_PARAMS = """\
    score_id,
    account_id,
    online_checksum,
    beatmap_md5,
    score,
    performance_points,
    accuracy,
    highest_combo,
    full_combo,
    mods,
    num_300s,
    num_100s,
    num_50s,
    num_misses,
    num_gekis,
    num_katus,
    grade,
    submission_status,
    game_mode,
    country,
    time_elapsed,
    client_anticheat_flags,
    client_anticheat_token,
    created_at,
    updated_at
"""


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


class Score(TypedDict):
    score_id: int
    account_id: int
    online_checksum: str
    beatmap_md5: str
    score: int
    performance_points: float
    accuracy: float
    highest_combo: int
    full_combo: bool
    mods: int
    num_300s: int
    num_100s: int
    num_50s: int
    num_misses: int
    num_gekis: int
    num_katus: int
    grade: str  # enum
    submission_status: int  # enum
    game_mode: int  # enum
    country: str
    time_elapsed: int
    client_anticheat_flags: int
    client_anticheat_token: str | None
    created_at: datetime
    updated_at: datetime


def deserialize(score: dict) -> Score:
    return {
        "score_id": score["score_id"],
        "account_id": score["account_id"],
        "online_checksum": score["online_checksum"],
        "beatmap_md5": score["beatmap_md5"],
        "score": score["score"],
        "performance_points": float(score["performance_points"]),
        "accuracy": float(score["accuracy"]),
        "highest_combo": score["highest_combo"],
        "full_combo": score["full_combo"],
        "mods": score["mods"],
        "num_300s": score["num_300s"],
        "num_100s": score["num_100s"],
        "num_50s": score["num_50s"],
        "num_misses": score["num_misses"],
        "num_gekis": score["num_gekis"],
        "num_katus": score["num_katus"],
        "grade": score["grade"],
        "submission_status": score["submission_status"],
        "game_mode": score["game_mode"],
        "country": score["country"],
        "time_elapsed": score["time_elapsed"],
        "client_anticheat_flags": score["client_anticheat_flags"],
        "client_anticheat_token": score["client_anticheat_token"],
        "created_at": score["created_at"],
        "updated_at": score["updated_at"],
    }


def serialize(score: Score) -> dict:
    return {
        "score_id": score["score_id"],
        "account_id": score["account_id"],
        "online_checksum": score["online_checksum"],
        "beatmap_md5": score["beatmap_md5"],
        "score": score["score"],
        "performance_points": score["performance_points"],  # should not need to decimal
        "accuracy": score["accuracy"],  # should not need to decimal
        "highest_combo": score["highest_combo"],
        "full_combo": score["full_combo"],
        "mods": score["mods"],
        "num_300s": score["num_300s"],
        "num_100s": score["num_100s"],
        "num_50s": score["num_50s"],
        "num_misses": score["num_misses"],
        "num_gekis": score["num_gekis"],
        "num_katus": score["num_katus"],
        "grade": score["grade"],
        "submission_status": score["submission_status"],
        "game_mode": score["game_mode"],
        "country": score["country"],
        "time_elapsed": score["time_elapsed"],
        "client_anticheat_flags": score["client_anticheat_flags"],
        "client_anticheat_token": score["client_anticheat_token"],
        "created_at": score["created_at"],
        "updated_at": score["updated_at"],
    }


async def create(
    account_id: int,
    online_checksum: str,
    beatmap_md5: str,
    score: int,
    performance_points: float,
    accuracy: float,
    highest_combo: int,
    full_combo: bool,
    mods: int,
    num_300s: int,
    num_100s: int,
    num_50s: int,
    num_misses: int,
    num_gekis: int,
    num_katus: int,
    grade: str,  # enum
    submission_status: int,  # enum
    game_mode: int,  # enum
    country: str,
    time_elapsed: int,
    client_anticheat_flags: int,
    client_anticheat_token: str | None,
) -> Score:
    _score = await clients.database.fetch_one(
        query=f"""
            INSERT INTO scores (account_id, online_checksum, beatmap_md5, score,
                                performance_points, accuracy, highest_combo,
                                full_combo, mods, num_300s, num_100s, num_50s,
                                num_misses, num_gekis, num_katus, grade,
                                submission_status, game_mode, country,
                                time_elapsed, client_anticheat_flags, client_anticheat_token)
            VALUES (:account_id, :online_checksum, :beatmap_md5, :score,
                    :performance_points, :accuracy, :highest_combo,
                    :full_combo, :mods, :num_300s, :num_100s, :num_50s,
                    :num_misses, :num_gekis, :num_katus, :grade,
                    :submission_status, :game_mode, :country,
                    :time_elapsed, :client_anticheat_flags, :client_anticheat_token)
            RETURNING {READ_PARAMS}
        """,
        values={
            "account_id": account_id,
            "online_checksum": online_checksum,
            "beatmap_md5": beatmap_md5,
            "score": score,
            "performance_points": performance_points,
            "accuracy": accuracy,
            "highest_combo": highest_combo,
            "full_combo": full_combo,
            "mods": mods,
            "num_300s": num_300s,
            "num_100s": num_100s,
            "num_50s": num_50s,
            "num_misses": num_misses,
            "num_gekis": num_gekis,
            "num_katus": num_katus,
            "grade": grade,
            "submission_status": submission_status,
            "game_mode": game_mode,
            "country": country,
            "time_elapsed": time_elapsed,
            "client_anticheat_flags": client_anticheat_flags,
            "client_anticheat_token": client_anticheat_token,
        },
    )
    assert _score is not None
    return deserialize(_score)


async def fetch_many(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
    friends: set[int] | None = None,
    sort_by: Literal[
        "score",
        "performance_points",
        "accuracy",
        "highest_combo",
        "grade",
    ] = "performance_points",
    page: int | None = None,
    page_size: int | None = None,
) -> list[Score]:
    if sort_by not in (
        "score",
        "performance_points",
        "accuracy",
        "highest_combo",
        "grade",
    ):
        raise ValueError(f"{sort_by} is not a valid value for sort_by parameter")

    query = f"""\
        SELECT {READ_PARAMS}
        FROM scores
        WHERE beatmap_md5 = COALESCE(:beatmap_md5, beatmap_md5)
        AND account_id = COALESCE(:account_id, account_id)
        AND country = COALESCE(:country, country)
        AND full_combo = COALESCE(:full_combo, full_combo)
        AND grade = COALESCE(:grade, grade)
        AND submission_status = COALESCE(:submission_status, submission_status)
        AND game_mode = COALESCE(:game_mode, game_mode)
        AND mods = COALESCE(:mods, mods)
    """
    values = {
        "beatmap_md5": beatmap_md5,
        "account_id": account_id,
        "country": country,
        "full_combo": full_combo,
        "grade": grade,
        "submission_status": submission_status,
        "game_mode": game_mode,
        "mods": mods,
    }
    if friends is not None:
        query += f"""\
            AND account_id = ANY(:friends)
        """
        values["friends"] = friends
    query += f"""\
        ORDER BY {sort_by} DESC
    """
    if page is not None and page_size is not None:
        query += f"""\
            LIMIT :page_size
            OFFSET :offset
        """
        values["page_size"] = page_size
        values["offset"] = page * page_size
    scores = await clients.database.fetch_all(query, values)
    return [deserialize(score) for score in scores]


async def fetch_count(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
) -> int:
    query = f"""\
        SELECT COUNT(*) AS count
        FROM scores
        WHERE beatmap_md5 = COALESCE(:beatmap_md5, beatmap_md5)
        AND account_id = COALESCE(:account_id, account_id)
        AND country = COALESCE(:country, country)
        AND full_combo = COALESCE(:full_combo, full_combo)
        AND grade = COALESCE(:grade, grade)
        AND submission_status = COALESCE(:submission_status, submission_status)
        AND game_mode = COALESCE(:game_mode, game_mode)
        AND mods = COALESCE(:mods, mods)
    """
    values = {
        "beatmap_md5": beatmap_md5,
        "account_id": account_id,
        "country": country,
        "full_combo": full_combo,
        "grade": grade,
        "submission_status": submission_status,
        "game_mode": game_mode,
        "mods": mods,
    }
    rec = await clients.database.fetch_one(query, values)
    assert rec is not None
    return rec["count"]


async def fetch_one_by_id(score_id: int) -> Score | None:
    score = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM scores
            WHERE score_id = :score_id
        """,
        values={
            "score_id": score_id,
        },
    )
    return deserialize(score) if score is not None else None
