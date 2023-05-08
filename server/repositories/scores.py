from datetime import datetime
from typing import cast
from typing import Literal
from typing import TypedDict

from server import clients

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
    created_at,
    updated_at
"""


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
    created_at: datetime
    updated_at: datetime


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
) -> Score:
    _score = await clients.database.fetch_one(
        query=f"""
            INSERT INTO scores (account_id, online_checksum, beatmap_md5, score,
                                performance_points, accuracy, highest_combo,
                                full_combo, mods, num_300s, num_100s, num_50s,
                                num_misses, num_gekis, num_katus, grade,
                                submission_status, game_mode, country,
                                time_elapsed, client_anticheat_flags)
            VALUES (:account_id, :online_checksum, :beatmap_md5, :score,
                    :performance_points, :accuracy, :highest_combo,
                    :full_combo, :mods, :num_300s, :num_100s, :num_50s,
                    :num_misses, :num_gekis, :num_katus, :grade,
                    :submission_status, :game_mode, :country,
                    :time_elapsed, :client_anticheat_flags)
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
        },
    )
    assert _score is not None
    return cast(Score, _score)


async def fetch_many(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
    sort_by: (
        Literal[
            "score",
            "performance_points",
            "accuracy",
            "highest_combo",
            "grade",
        ]
        | None
    ) = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[Score]:
    assert sort_by in (
        "score",
        "performance_points",
        "accuracy",
        "highest_combo",
        "grade",
    )
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
        ORDER BY {sort_by} DESC
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
    if page is not None and page_size is not None:
        query += f"""\
            LIMIT :page_size
            OFFSET :offset
        """
        values["page_size"] = page_size
        values["offset"] = page * page_size
    scores = await clients.database.fetch_all(query, values)
    return cast(list[Score], scores)


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
    return cast(Score, score) if score is not None else None
