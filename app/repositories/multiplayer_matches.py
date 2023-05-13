import json
from datetime import datetime
from typing import cast
from typing import Literal
from typing import TypedDict

from app import clients


# TODO: a subset of the data here needs to be persisted to the database
# this will be useful for the match history page
class MultiplayerMatch(TypedDict):
    match_id: int
    match_name: str
    match_password: str
    beatmap_name: str
    beatmap_id: int
    beatmap_md5: str
    host_account_id: int
    game_mode: int  # enum
    mods: int  # flags
    win_condition: int  # enum
    team_type: int  # enum
    freemods_enabled: bool
    random_seed: int
    status: int  # enum
    created_at: datetime
    updated_at: datetime


class MatchStatus:
    WAITING = 0
    PLAYING = 1


class MatchTeamTypes:
    HEAD_TO_HEAD = 0
    TAG_COOP = 1
    TEAM_VS = 2
    TAG_TEAM_VS = 3


class MatchWinCondition:
    SCORE = 0
    ACCURACY = 1
    COMBO = 2
    SCORE_V2 = 3


class MatchTeams:
    NEUTRAL = 0
    BLUE = 1
    RED = 2


def make_key(match_id: int | Literal["*"]) -> str:
    return f"server:matches:{match_id}"


def serialize(match: MultiplayerMatch) -> str:
    return json.dumps(
        {
            "match_id": match["match_id"],
            "match_name": match["match_name"],
            "match_password": match["match_password"],
            "beatmap_name": match["beatmap_name"],
            "beatmap_id": match["beatmap_id"],
            "beatmap_md5": match["beatmap_md5"],
            "host_account_id": match["host_account_id"],
            "game_mode": match["game_mode"],
            "mods": match["mods"],
            "win_condition": match["win_condition"],
            "team_type": match["team_type"],
            "freemods_enabled": match["freemods_enabled"],
            "random_seed": match["random_seed"],
            "status": match["status"],
        }
    )


def deserialize(raw_match: str) -> MultiplayerMatch:
    match = json.loads(raw_match)

    assert isinstance(match, dict)

    return cast(MultiplayerMatch, match)


async def create(
    match_id: int,
    match_name: str,
    match_password: str,
    beatmap_name: str,
    beatmap_id: int,
    beatmap_md5: str,
    host_account_id: int,
    game_mode: int,  # enum
    mods: int,  # flags
    win_condition: int,  # enum
    team_type: int,  # enum
    freemods_enabled: bool,
    random_seed: int,
) -> MultiplayerMatch:
    now = datetime.now()
    match: MultiplayerMatch = {
        "match_id": match_id,
        "match_name": match_name,
        "match_password": match_password,
        "beatmap_id": beatmap_id,
        "beatmap_name": beatmap_name,
        "beatmap_md5": beatmap_md5,
        "host_account_id": host_account_id,
        "game_mode": game_mode,
        "mods": mods,
        "win_condition": win_condition,
        "team_type": team_type,
        "freemods_enabled": freemods_enabled,
        "random_seed": random_seed,
        "status": MatchStatus.WAITING,
        "created_at": now,
        "updated_at": now,
    }

    await clients.redis.set(
        name=make_key(match_id),
        value=serialize(match),
    )

    return match
    # MetalFace Was Here


async def fetch_one(match_id: int) -> MultiplayerMatch | None:
    raw_match = await clients.redis.get(make_key(match_id))

    if raw_match is None:
        return None

    return deserialize(raw_match)


async def fetch_all() -> list[MultiplayerMatch]:
    match_key = make_key("*")

    cursor = None
    matches = []

    while cursor != 0:
        cursor, keys = await clients.redis.scan(
            cursor=cursor or 0,
            match=match_key,
        )

        raw_matches = await clients.redis.mget(keys)

        for raw_match in raw_matches:
            assert raw_match is not None  # TODO: why does mget return list[T | None]?
            match = deserialize(raw_match)

            matches.append(match)

    return matches


async def partial_update(
    match_id: int,
    match_name: str | None,
    match_password: str | None,
    beatmap_name: str | None,
    beatmap_id: int | None,
    beatmap_md5: str | None,
    host_account_id: int | None,
    game_mode: int | None,  # enum
    mods: int | None,  # flags
    win_condition: int | None,  # enum
    team_type: int | None,  # enum
    freemods_enabled: bool | None,
    random_seed: int | None,
    status: int | None,  # enum
) -> MultiplayerMatch | None:
    match_key = make_key(match_id)

    raw_match = await clients.redis.get(match_key)

    if raw_match is None:
        return None

    match = deserialize(raw_match)

    if match_name is not None:
        match["match_name"] = match_name

    if match_password is not None:
        match["match_password"] = match_password

    if beatmap_name is not None:
        match["beatmap_name"] = beatmap_name

    if beatmap_id is not None:
        match["beatmap_id"] = beatmap_id

    if beatmap_md5 is not None:
        match["beatmap_md5"] = beatmap_md5

    if host_account_id is not None:
        match["host_account_id"] = host_account_id

    if game_mode is not None:
        match["game_mode"] = game_mode

    if mods is not None:
        match["mods"] = mods

    if win_condition is not None:
        match["win_condition"] = win_condition

    if team_type is not None:
        match["team_type"] = team_type

    if freemods_enabled is not None:
        match["freemods_enabled"] = freemods_enabled

    if random_seed is not None:
        match["random_seed"] = random_seed

    if status is not None:
        match["status"] = status

    match["updated_at"] = datetime.now()

    await clients.redis.set(
        name=make_key(match_id),
        value=serialize(match),
    )

    return match


async def delete(match_id: int) -> MultiplayerMatch | None:
    match_key = make_key(match_id)

    raw_match = await clients.redis.get(match_key)

    if raw_match is None:
        return None

    await clients.redis.delete(match_key)

    return deserialize(raw_match)
