from datetime import datetime
from typing import Literal
from typing import TypedDict

from app import clients

READ_PARAMS = """\
    s.score_id,
    s.account_id,
    s.online_checksum,
    s.beatmap_md5,
    s.score,
    s.performance_points,
    s.accuracy,
    s.highest_combo,
    s.full_combo,
    s.mods,
    s.num_300s,
    s.num_100s,
    s.num_50s,
    s.num_misses,
    s.num_gekis,
    s.num_katus,
    s.grade,
    s.submission_status,
    s.game_mode,
    s.country,
    s.time_elapsed,
    s.client_anticheat_flags,
    s.client_anticheat_token,
    s.created_at,
    s.updated_at,

    b.beatmap_set_id AS beatmap_set_id,
    b.ranked_status AS beatmap_ranked_status,
    b.artist AS beatmap_artist,
    b.title AS beatmap_title,
    b.version AS beatmap_version,
    b.creator AS beatmap_creator,
    b.max_combo AS beatmap_max_combo,
    b.bpm AS beatmap_bpm,
    b.cs AS beatmap_cs,
    b.ar AS beatmap_ar,
    b.od AS beatmap_od,
    b.hp AS beatmap_hp,
    b.star_rating AS beatmap_star_rating
"""


class SubmissionStatus:
    FAILED = 0
    SUBMITTED = 1
    BEST = 2


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

    # beatmap attrs; here for convenience
    beatmap_set_id: int
    beatmap_ranked_status: int
    beatmap_artist: str
    beatmap_title: str
    beatmap_version: str
    beatmap_creator: str
    beatmap_max_combo: int
    beatmap_bpm: float
    beatmap_cs: float
    beatmap_ar: float
    beatmap_od: float
    beatmap_hp: float
    beatmap_star_rating: float


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
        # beatmap attrs; here for convenience
        "beatmap_set_id": score["beatmap_set_id"],
        "beatmap_ranked_status": score["beatmap_ranked_status"],
        "beatmap_artist": score["beatmap_artist"],
        "beatmap_title": score["beatmap_title"],
        "beatmap_version": score["beatmap_version"],
        "beatmap_creator": score["beatmap_creator"],
        "beatmap_max_combo": score["beatmap_max_combo"],
        "beatmap_bpm": score["beatmap_bpm"],
        "beatmap_cs": score["beatmap_cs"],
        "beatmap_ar": score["beatmap_ar"],
        "beatmap_od": score["beatmap_od"],
        "beatmap_hp": score["beatmap_hp"],
        "beatmap_star_rating": score["beatmap_star_rating"],
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
        # beatmap attrs; here for convenience
        "beatmap_set_id": score["beatmap_set_id"],
        "beatmap_ranked_status": score["beatmap_ranked_status"],
        "beatmap_artist": score["beatmap_artist"],
        "beatmap_title": score["beatmap_title"],
        "beatmap_version": score["beatmap_version"],
        "beatmap_creator": score["beatmap_creator"],
        "beatmap_max_combo": score["beatmap_max_combo"],
        "beatmap_bpm": score["beatmap_bpm"],
        "beatmap_cs": score["beatmap_cs"],
        "beatmap_ar": score["beatmap_ar"],
        "beatmap_od": score["beatmap_od"],
        "beatmap_hp": score["beatmap_hp"],
        "beatmap_star_rating": score["beatmap_star_rating"],
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
            WITH inserted AS (
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
            )
            SELECT {READ_PARAMS}
              FROM inserted s
         LEFT JOIN beatmaps b ON s.beatmap_md5 = b.beatmap_md5
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
    game_mode: int | None = None,
    mods: int | None = None,
    submission_statuses: list[int] | None = None,
    friends: list[int] | None = None,
    beatmap_ranked_status: int | None = None,
    beatmap_set_id: int | None = None,
    sort_by: Literal[
        "score",
        "performance_points",
        "accuracy",
        "highest_combo",
        "grade",
        "created_at",
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
        "created_at",
    ):
        raise ValueError(f"{sort_by} is not a valid value for sort_by parameter")

    query = f"""\
        SELECT {READ_PARAMS}
        FROM scores s
        LEFT JOIN beatmaps b ON b.beatmap_md5 = s.beatmap_md5
        WHERE s.beatmap_md5 = COALESCE(:beatmap_md5, s.beatmap_md5)
        AND s.account_id = COALESCE(:account_id, s.account_id)
        AND s.country = COALESCE(:country, s.country)
        AND s.full_combo = COALESCE(:full_combo, s.full_combo)
        AND s.grade = COALESCE(:grade, s.grade)
        AND s.game_mode = COALESCE(:game_mode, s.game_mode)
        AND s.mods = COALESCE(:mods, s.mods)
        AND b.ranked_status = COALESCE(:beatmap_ranked_status, b.ranked_status)
        AND b.beatmap_set_id = COALESCE(:beatmap_set_id, b.beatmap_set_id)
    """
    values = {
        "beatmap_md5": beatmap_md5,
        "account_id": account_id,
        "country": country,
        "full_combo": full_combo,
        "grade": grade,
        "game_mode": game_mode,
        "mods": mods,
        "beatmap_ranked_status": beatmap_ranked_status,
        "beatmap_set_id": beatmap_set_id,
    }

    if submission_statuses is not None:
        query += f"""\
            AND s.submission_status = ANY(:submission_statuses)
        """
        values["submission_statuses"] = submission_statuses

    if friends is not None:
        query += f"""\
            AND s.account_id = ANY(:friends)
        """
        values["friends"] = friends

    query += f"""\
        ORDER BY s.{sort_by} DESC
    """

    if page is not None and page_size is not None:
        query += f"""\
            LIMIT :page_size
            OFFSET :offset
        """
        values["page_size"] = page_size
        values["offset"] = (page - 1) * page_size

    scores = await clients.database.fetch_all(query, values)
    return [deserialize(score) for score in scores]


async def fetch_total_count(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
    submission_statuses: list[int] | None = None,
    friends: list[int] | None = None,
    beatmap_ranked_status: int | None = None,
    beatmap_set_id: int | None = None,
) -> int:
    query = f"""\
        SELECT COUNT(*) AS count
        FROM scores AS s
        LEFT JOIN beatmaps AS b USING(beatmap_md5)
        WHERE s.beatmap_md5 = COALESCE(:beatmap_md5, s.beatmap_md5)
        AND s.account_id = COALESCE(:account_id, s.account_id)
        AND s.country = COALESCE(:country, s.country)
        AND s.full_combo = COALESCE(:full_combo, s.full_combo)
        AND s.grade = COALESCE(:grade, s.grade)
        AND s.game_mode = COALESCE(:game_mode, s.game_mode)
        AND s.mods = COALESCE(:mods, s.mods)
        AND b.ranked_status = COALESCE(:beatmap_ranked_status, b.ranked_status)
        AND b.beatmap_set_id = COALESCE(:beatmap_set_id, b.beatmap_set_id)
    """
    values = {
        "beatmap_md5": beatmap_md5,
        "account_id": account_id,
        "country": country,
        "full_combo": full_combo,
        "grade": grade,
        "game_mode": game_mode,
        "mods": mods,
        "beatmap_ranked_status": beatmap_ranked_status,
        "beatmap_set_id": beatmap_set_id,
    }

    if submission_statuses is not None:
        query += f"""\
            AND submission_status = ANY(:submission_statuses)
        """
        values["submission_statuses"] = submission_statuses

    if friends is not None:
        query += f"""\
            AND account_id = ANY(:friends)
        """
        values["friends"] = friends

    rec = await clients.database.fetch_one(query, values)
    assert rec is not None
    return rec["count"]


# TODO: fetch_count for this
async def fetch_best_for_each_account(
    beatmap_md5: str | None = None,
    account_id: int | None = None,
    country: str | None = None,
    full_combo: bool | None = None,
    grade: str | None = None,
    submission_statuses: list[int] | None = None,
    game_mode: int | None = None,
    mods: int | None = None,
    friends: list[int] | None = None,
    beatmap_ranked_status: int | None = None,
    beatmap_set_id: int | None = None,
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
        WITH selected_scores AS (
            SELECT DISTINCT ON (s.account_id) {READ_PARAMS}
            FROM scores AS s
            LEFT JOIN beatmaps AS b USING(beatmap_md5)
            WHERE s.beatmap_md5 = COALESCE(:beatmap_md5, s.beatmap_md5)
            AND s.account_id = COALESCE(:account_id, s.account_id)
            AND s.country = COALESCE(:country, s.country)
            AND s.full_combo = COALESCE(:full_combo, s.full_combo)
            AND s.grade = COALESCE(:grade, s.grade)
            AND s.game_mode = COALESCE(:game_mode, s.game_mode)
            AND s.mods = COALESCE(:mods, s.mods)
            AND b.ranked_status = COALESCE(:beatmap_ranked_status, b.ranked_status)
            AND b.beatmap_set_id = COALESCE(:beatmap_set_id, b.beatmap_set_id)
    """
    values = {
        "beatmap_md5": beatmap_md5,
        "account_id": account_id,
        "country": country,
        "full_combo": full_combo,
        "grade": grade,
        "game_mode": game_mode,
        "mods": mods,
        "beatmap_ranked_status": beatmap_ranked_status,
        "beatmap_set_id": beatmap_set_id,
    }

    if submission_statuses is not None:
        query += f"""\
            AND submission_status = ANY(:submission_statuses)
        """
        values["submission_statuses"] = submission_statuses

    if friends is not None:
        query += f"""\
            AND account_id = ANY(:friends)
        """
        values["friends"] = friends

    query += f"""\
            ORDER BY account_id, {sort_by} DESC
        )
        SELECT {READ_PARAMS} FROM selected_scores
        ORDER BY {sort_by} DESC
    """

    if page is not None and page_size is not None:
        query += f"""\
            LIMIT :page_size
            OFFSET :offset
        """
        values["page_size"] = page_size
        values["offset"] = (page - 1) * page_size

    scores = await clients.database.fetch_all(query, values)
    return [deserialize(score) for score in scores]


async def fetch_one_by_id(score_id: int) -> Score | None:
    score = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
              FROM scores s
         LEFT JOIN beatmaps b ON s.beatmap_md5 = b.beatmap_md5
             WHERE score_id = :score_id
        """,
        values={
            "score_id": score_id,
        },
    )
    return deserialize(score) if score is not None else None


async def partial_update(
    score_id: int,
    # TODO: probably not all of this should be updatable
    score: int | None = None,
    performance_points: float | None = None,
    accuracy: float | None = None,
    highest_combo: int | None = None,
    full_combo: bool | None = None,
    mods: int | None = None,
    num_300s: int | None = None,
    num_100s: int | None = None,
    num_50s: int | None = None,
    num_misses: int | None = None,
    num_gekis: int | None = None,
    num_katus: int | None = None,
    grade: str | None = None,  # enum
    submission_status: int | None = None,  # enum
    game_mode: int | None = None,  # enum
    country: str | None = None,
    time_elapsed: int | None = None,
    client_anticheat_flags: int | None = None,
    client_anticheat_token: str | None = None,
) -> Score | None:
    _score = await clients.database.fetch_one(
        query=f"""
            UPDATE scores s
            SET score = COALESCE(:score, score),
                performance_points = COALESCE(:performance_points, performance_points),
                accuracy = COALESCE(:accuracy, accuracy),
                highest_combo = COALESCE(:highest_combo, highest_combo),
                full_combo = COALESCE(:full_combo, full_combo),
                mods = COALESCE(:mods, mods),
                num_300s = COALESCE(:num_300s, num_300s),
                num_100s = COALESCE(:num_100s, num_100s),
                num_50s = COALESCE(:num_50s, num_50s),
                num_misses = COALESCE(:num_misses, num_misses),
                num_gekis = COALESCE(:num_gekis, num_gekis),
                num_katus = COALESCE(:num_katus, num_katus),
                grade = COALESCE(:grade, grade),
                submission_status = COALESCE(:submission_status, submission_status),
                game_mode = COALESCE(:game_mode, game_mode),
                country = COALESCE(:country, country),
                time_elapsed = COALESCE(:time_elapsed, time_elapsed),
                client_anticheat_flags = COALESCE(:client_anticheat_flags, client_anticheat_flags),
                client_anticheat_token = COALESCE(:client_anticheat_token, client_anticheat_token)
           FROM beatmaps b
          WHERE s.beatmap_md5 = b.beatmap_md5
            AND score_id = :score_id
      RETURNING {READ_PARAMS}
        """,
        values={
            "score_id": score_id,
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
    return deserialize(_score) if _score is not None else None
