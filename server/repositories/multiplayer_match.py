from typing import Literal, TypedDict
import json
from typing import cast
from server.repositories import multiplayer_match_ids
from server import clients


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
    freemods_allowed: bool
    random_seed: int


def make_key(match_id: int | Literal["*"]) -> str:
    return f"server:multiplayer_match:{match_id}"


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
            "freemods_allowed": match["freemods_allowed"],
            "random_seed": match["random_seed"],
        }
    )


def deserialize(raw_match: str) -> MultiplayerMatch:
    match = json.loads(raw_match)

    assert isinstance(match, dict)

    return cast(MultiplayerMatch, match)


async def create(
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
    freemods_allowed: bool,
    random_seed: int,
) -> MultiplayerMatch:
    multiplayer_match_id = await multiplayer_match_ids.claim_id()

    assert multiplayer_match_id is not None

    multiplayer_match: MultiplayerMatch = {
        "match_id": multiplayer_match_id,
        "match_name": match_name,
        "match_password": match_password,
        "beatmap_name": beatmap_name,
        "beatmap_id": beatmap_id,
        "beatmap_name": beatmap_name,
        "beatmap_id": beatmap_id,
        "beatmap_md5": beatmap_md5,
        "host_account_id": host_account_id,
        "game_mode": game_mode,
        "mods": mods,
        "game_mode": game_mode,
        "mods": mods,
        "win_condition": win_condition,
        "team_type": team_type,
        "freemods_allowed": freemods_allowed,
        "random_seed": random_seed,
    }

    await clients.redis.set(
        name=make_key(multiplayer_match_id),
        value=serialize(cast(MultiplayerMatch, multiplayer_match)),
    )

    return multiplayer_match
    # MetalFace Was Here


async def fetch_match_by_id(match_id: int) -> MultiplayerMatch | None:
    raw_match = await clients.redis.get(make_key(match_id))

    if raw_match is None:
        return None

    return deserialize(raw_match)

async def fetch_all_matches() -> list[MultiplayerMatch] | None:
    matches = []
    # need number of items in match id table
    clients.redis.mget

