from pydantic import BaseModel

# input models


# output models


class Stats(BaseModel):
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
    # account info; here for convenience
    username: str
