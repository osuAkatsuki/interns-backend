from typing import Literal, TypedDict
import json
from typing import cast


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


