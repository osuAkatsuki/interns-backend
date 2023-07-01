from typing import Literal
from typing import TypedDict

from app import clients
from app._typing import UNSET
from app._typing import Unset

READ_PARAMS = """\
    s.account_id,
    s.game_mode,
    s.total_score,
    s.ranked_score,
    s.performance_points,
    s.play_count,
    s.play_time,
    s.accuracy,
    s.highest_combo,
    s.total_hits,
    s.replay_views,
    s.xh_count,
    s.x_count,
    s.sh_count,
    s.s_count,
    s.a_count,

    -- account fields for convenience
    a.username
"""


class Stats(TypedDict):
    account_id: int
    game_mode: int
    total_score: int
    ranked_score: int
    performance_points: int
    play_count: int
    play_time: int
    accuracy: float
    highest_combo: int
    total_hits: int
    replay_views: int
    xh_count: int
    x_count: int
    sh_count: int
    s_count: int
    a_count: int

    # TODO: track updated_at?

    # account fields for convenience
    username: str


class StatsUpdateFields(TypedDict, total=False):
    total_score: int
    ranked_score: int
    performance_points: int
    play_count: int
    play_time: int
    accuracy: float
    highest_combo: int
    total_hits: int
    replay_views: int
    xh_count: int
    x_count: int
    sh_count: int
    s_count: int
    a_count: int


def serialize(stats: Stats) -> dict:
    return {
        "account_id": stats["account_id"],
        "game_mode": stats["game_mode"],
        "total_score": stats["total_score"],
        "ranked_score": stats["ranked_score"],
        "performance_points": stats["performance_points"],
        "play_count": stats["play_count"],
        "play_time": stats["play_time"],
        "accuracy": stats["accuracy"],  # should not need to be decimal
        "highest_combo": stats["highest_combo"],
        "total_hits": stats["total_hits"],
        "replay_views": stats["replay_views"],
        "xh_count": stats["xh_count"],
        "x_count": stats["x_count"],
        "sh_count": stats["sh_count"],
        "s_count": stats["s_count"],
        "a_count": stats["a_count"],
        "username": stats["username"],
    }


def deserialize(stats: dict) -> Stats:
    return {
        "account_id": stats["account_id"],
        "game_mode": stats["game_mode"],
        "total_score": stats["total_score"],
        "ranked_score": stats["ranked_score"],
        "performance_points": stats["performance_points"],
        "play_count": stats["play_count"],
        "play_time": stats["play_time"],
        "accuracy": float(stats["accuracy"]),
        "highest_combo": stats["highest_combo"],
        "total_hits": stats["total_hits"],
        "replay_views": stats["replay_views"],
        "xh_count": stats["xh_count"],
        "x_count": stats["x_count"],
        "sh_count": stats["sh_count"],
        "s_count": stats["s_count"],
        "a_count": stats["a_count"],
        "username": stats["username"],
    }


async def create(account_id: int, game_mode: int) -> Stats:
    stats = await clients.database.fetch_one(
        query=f"""\
            WITH inserted AS (
                INSERT INTO stats (account_id, game_mode)
                VALUES (:account_id, :game_mode)
                RETURNING *
            )
            SELECT {READ_PARAMS}
              FROM inserted s
         LEFT JOIN accounts a ON s.account_id = a.account_id
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
        },
    )

    assert stats is not None
    return deserialize(stats)


# TODO: combine these


async def fetch_all(
    account_id: int | None = None,
    game_mode: int | None = None,
) -> list[Stats]:
    all_stats = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
              FROM stats s
         LEFT JOIN accounts a ON s.account_id = a.accounts_id
             WHERE s.account_id = COALESCE(:account_id, s.account_id)
               AND s.game_mode = COALESCE(:game_mode, s.game_mode)
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
        },
    )
    return [deserialize(stats) for stats in all_stats]


def validate_sort_params(sort_by: str, sort_order: str) -> None:
    if sort_by not in (
        "total_score",
        "ranked_score",
        "performance_points",
        "play_count",
        "play_time",
        "accuracy",
        "highest_combo",
        "total_hits",
        "replay_views",
        "xh_count",
        "x_count",
        "sh_count",
        "s_count",
        "a_count",
    ):
        raise ValueError("Invalid sort_by")

    if sort_order not in ("asc", "desc"):
        raise ValueError("Invalid sort_order")


async def fetch_many(
    account_id: int | None = None,
    game_mode: int | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: Literal[
        "total_score",
        "ranked_score",
        "performance_points",
        "play_count",
        "play_time",
        "accuracy",
        "highest_combo",
        "total_hits",
        "replay_views",
        "xh_count",
        "x_count",
        "sh_count",
        "s_count",
        "a_count",
    ] = "performance_points",
    sort_order: Literal["asc", "desc"] = "desc",
) -> list[Stats]:
    validate_sort_params(sort_by, sort_order)  # just in case
    all_stats = await clients.database.fetch_all(
        query=f"""
            SELECT {READ_PARAMS}
              FROM stats s
         LEFT JOIN accounts a ON s.account_id = a.account_id
             WHERE s.account_id = COALESCE(:account_id, s.account_id)
               AND s.game_mode = COALESCE(:game_mode, s.game_mode)
             ORDER BY s.{sort_by} {sort_order}
             LIMIT :limit
            OFFSET :offset
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )
    return [deserialize(stats) for stats in all_stats]


async def fetch_total_count(
    account_id: int | None = None,
    game_mode: int | None = None,
) -> int:
    rec = await clients.database.fetch_one(
        query=f"""
            SELECT COUNT(*) AS count
              FROM stats s
         LEFT JOIN accounts a ON s.account_id = a.account_id
             WHERE s.account_id = COALESCE(:account_id, s.account_id)
               AND s.game_mode = COALESCE(:game_mode, s.game_mode)
        """,
        values={
            "account_id": account_id,
            "game_mode": game_mode,
        },
    )
    assert rec is not None
    return rec["count"]


async def fetch_one(account_id: int, game_mode: int) -> Stats | None:
    stats = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
              FROM stats s
         LEFT JOIN accounts a ON s.account_id = a.accounts_id
             WHERE s.account_id = :account_id
               AND s.game_mode = :game_mode
        """,
        values={"account_id": account_id, "game_mode": game_mode},
    )
    return deserialize(stats) if stats is not None else None


async def partial_update(
    account_id: int,
    game_mode: int,
    total_score: int | Unset = UNSET,
    ranked_score: int | Unset = UNSET,
    performance_points: int | Unset = UNSET,
    play_count: int | Unset = UNSET,
    play_time: int | Unset = UNSET,
    accuracy: float | Unset = UNSET,
    highest_combo: int | Unset = UNSET,
    total_hits: int | Unset = UNSET,
    replay_views: int | Unset = UNSET,
    xh_count: int | Unset = UNSET,
    x_count: int | Unset = UNSET,
    sh_count: int | Unset = UNSET,
    s_count: int | Unset = UNSET,
    a_count: int | Unset = UNSET,
) -> Stats | None:
    update_fields: StatsUpdateFields = {}
    if not isinstance(total_score, Unset):
        update_fields["total_score"] = total_score
    if not isinstance(ranked_score, Unset):
        update_fields["ranked_score"] = ranked_score
    if not isinstance(performance_points, Unset):
        update_fields["performance_points"] = performance_points
    if not isinstance(play_count, Unset):
        update_fields["play_count"] = play_count
    if not isinstance(play_time, Unset):
        update_fields["play_time"] = play_time
    if not isinstance(accuracy, Unset):
        update_fields["accuracy"] = accuracy
    if not isinstance(highest_combo, Unset):
        update_fields["highest_combo"] = highest_combo
    if not isinstance(total_hits, Unset):
        update_fields["total_hits"] = total_hits
    if not isinstance(replay_views, Unset):
        update_fields["replay_views"] = replay_views
    if not isinstance(xh_count, Unset):
        update_fields["xh_count"] = xh_count
    if not isinstance(x_count, Unset):
        update_fields["x_count"] = x_count
    if not isinstance(sh_count, Unset):
        update_fields["sh_count"] = sh_count
    if not isinstance(s_count, Unset):
        update_fields["s_count"] = s_count
    if not isinstance(a_count, Unset):
        update_fields["a_count"] = a_count

    stats = await clients.database.fetch_one(
        query=f"""\
            UPDATE stats s
               SET {",".join(f"{k} = :{k}" for k in update_fields)}
              FROM accounts a
         LEFT JOIN accounts a ON s.account_id = a.accounts_id
             WHERE s.account_id = :account_id
               AND s.game_mode = :game_mode
         RETURNING {READ_PARAMS}
        """,
        values={"account_id": account_id, "game_mode": game_mode} | update_fields,
    )
    return deserialize(stats) if stats is not None else None
