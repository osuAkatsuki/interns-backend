import json
from datetime import datetime
from typing import cast
from typing import Literal
from typing import TypedDict

from app import clients
from app.typing import UNSET
from app.typing import Unset


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
    match_name: str | Unset = UNSET,
    match_password: str | Unset = UNSET,
    beatmap_name: str | Unset = UNSET,
    beatmap_id: int | Unset = UNSET,
    beatmap_md5: str | Unset = UNSET,
    host_account_id: int | Unset = UNSET,
    game_mode: int | Unset = UNSET,  # enum
    mods: int | Unset = UNSET,  # flags
    win_condition: int | Unset = UNSET,  # enum
    team_type: int | Unset = UNSET,  # enum
    freemods_enabled: bool | Unset = UNSET,
    random_seed: int | Unset = UNSET,
    status: int | Unset = UNSET,  # enum
) -> MultiplayerMatch | None:
    match_key = make_key(match_id)

    raw_match = await clients.redis.get(match_key)

    if raw_match is None:
        return None

    match = deserialize(raw_match)

    if not isinstance(match_name, Unset):
        match["match_name"] = match_name
    if not isinstance(match_password, Unset):
        match["match_password"] = match_password
    if not isinstance(beatmap_name, Unset):
        match["beatmap_name"] = beatmap_name
    if not isinstance(beatmap_id, Unset):
        match["beatmap_id"] = beatmap_id
    if not isinstance(beatmap_md5, Unset):
        match["beatmap_md5"] = beatmap_md5
    if not isinstance(host_account_id, Unset):
        match["host_account_id"] = host_account_id
    if not isinstance(game_mode, Unset):
        match["game_mode"] = game_mode
    if not isinstance(mods, Unset):
        match["mods"] = mods
    if not isinstance(win_condition, Unset):
        match["win_condition"] = win_condition
    if not isinstance(team_type, Unset):
        match["team_type"] = team_type
    if not isinstance(freemods_enabled, Unset):
        match["freemods_enabled"] = freemods_enabled
    if not isinstance(random_seed, Unset):
        match["random_seed"] = random_seed
    if not isinstance(status, Unset):
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
