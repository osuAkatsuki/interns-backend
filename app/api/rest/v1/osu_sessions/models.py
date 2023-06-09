from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# input models


# output models


class OsuSession(BaseModel):
    osu_session_id: UUID
    account_id: int
    username: str
    utc_offset: int
    country: str
    # privileges: int
    game_mode: int
    # latitude: float
    # longitude: float
    action: int
    info_text: str
    beatmap_md5: str
    beatmap_id: int
    mods: int
    # pm_private: bool
    # receive_match_updates: bool
    spectator_host_osu_session_id: UUID | None
    away_message: str | None
    multiplayer_match_id: int | None
    # last_communicated_at: datetime
    last_np_beatmap_id: int | None
    primary: bool

    expires_at: datetime
    created_at: datetime
    updated_at: datetime
