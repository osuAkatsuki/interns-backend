from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# input models


class LoginCredentials(BaseModel):
    username: str
    password: str


# output models


class WebSession(BaseModel):
    web_session_id: UUID
    account_id: int
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
