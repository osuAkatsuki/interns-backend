from datetime import datetime

from pydantic import BaseModel


# input models


# output models


class Account(BaseModel):
    account_id: int
    username: str
    # email_address: str
    privileges: int
    # password: str
    country: str
    created_at: datetime
    # updated_at: datetime
