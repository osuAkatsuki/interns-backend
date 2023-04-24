from typing import cast
from datetime import datetime
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
    play_time,
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
    submission_status: str  # enum
    game_mode: int  # enum
    play_time: int
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
    submission_status: str,  # enum
    game_mode: int,  # enum
    play_time: int,
    country: str,
    time_elapsed: int,
    client_anticheat_flags: int,
) -> Score:
    score = await clients.database.fetch_one(
        query=f"""
            INSERT INTO scores (account_id, online_checksum, beatmap_md5, score,
                                performance_points, accuracy, highest_combo,
                                full_combo, mods, num_300s, num_100s, num_50s,
                                num_misses, num_gekis, num_katus, grade,
                                submission_status, game_mode, play_time, country,
                                time_elapsed, client_anticheat_flags)
            VALUES (:account_id, :online_checksum, :beatmap_md5, :score,
                    performance_points, :accuracy, :highest_combo,
                    full_combo, :mods, :num_300s, :num_100s, :num_50s,
                    num_misses, :num_gekis, :num_katus, :grade,
                    submission_status, :game_mode, :play_time, :country,
                    time_elapsed, :client_anticheat_flags)
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
            "play_time": play_time,
            "country": country,
            "time_elapsed": time_elapsed,
            "client_anticheat_flags": client_anticheat_flags,
        },
    )
    assert score is not None
    return cast(Score, score)


async def fetch_all(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_status: int | None = None,
    game_mode: int | None = None,
    country: str | None = None,
) -> list[Score]:
    scores = await clients.database.fetch_all(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM scores
            WHERE beatmap_md5 = COALESCE(:beatmap_md5, beatmap_md5)
            AND country = COALESCE(:country, country)
            AND full_combo = COALESCE(:full_combo, full_combo)
            AND grade = COALESCE(:grade, grade)
            AND submission_status = COALESCE(:submission_status, submission_status)
            AND game_mode = COALESCE(:game_mode, game_mode)
        """,
        values={
            "beatmap_md5": beatmap_md5,
            "account_id": account_id,
            "country": country,
            "full_combo": full_combo,
            "grade": grade,
            "submission_status": submission_status,
            "game_mode": game_mode,
        },
    )
    return [cast(Score, dict(score._mapping)) for score in scores]
