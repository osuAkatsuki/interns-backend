from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# input models


class LoginForm(BaseModel):
    username: str
    password: str


# TODO: PresenceUpdate, SessionUpdate models


# output models


class Presence(BaseModel):
    account_id: int
    username: str
    utc_offset: int
    country: str
    privileges: int
    game_mode: int
    latitude: float
    longitude: float
    action: int
    info_text: str
    beatmap_md5: str
    beatmap_id: int
    mods: int
    receive_match_updates: bool
    spectator_host_session_id: UUID | None
    away_message: str | None
    multiplayer_match_id: int | None
    last_communicated_at: datetime
    last_np_beatmap_id: int | None


class Session(BaseModel):
    session_id: UUID
    account_id: int
    presence: Presence
    expires_at: datetime
    created_at: datetime
    # updated_at: datetime
