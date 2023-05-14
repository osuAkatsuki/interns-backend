from datetime import datetime

from pydantic import BaseModel


# input models


# output models


class Score(BaseModel):
    score_id: int
    account_id: int
    # online_checksum: str
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
    # client_anticheat_flags: int
    created_at: datetime
    updated_at: datetime
