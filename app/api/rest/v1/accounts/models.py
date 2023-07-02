from datetime import datetime

from pydantic import BaseModel


# input models


class AccountInput(BaseModel):
    username: str
    email_address: str
    password: str
    country: str
    recaptcha_token: str


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
