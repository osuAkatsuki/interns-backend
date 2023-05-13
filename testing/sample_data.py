import random
import uuid
from typing import TYPE_CHECKING

from faker import Faker

from app import geolocation

if TYPE_CHECKING:
    from app.repositories.sessions import Session
    from app.repositories.accounts import Account

fake = Faker()


def fake_country() -> str:
    return random.choice(tuple(geolocation.COUNTRY_STR_TO_INT))


def fake_session() -> "Session":
    return {
        "session_id": uuid.uuid4(),
        "account_id": fake.pyint(),
        "presence": {
            "account_id": fake.pyint(),
            "username": fake.user_name(),
            "utc_offset": fake.pyint(),
            "country": fake.country(),
            "privileges": fake.pyint(),
            "game_mode": fake.pyint(),
            "latitude": fake.pyfloat(),
            "longitude": fake.pyfloat(),
            "action": fake.pyint(),
            "info_text": fake.text(),
            "beatmap_md5": fake.md5(),
            "beatmap_id": fake.pyint(),
            "mods": fake.pyint(),
            "mode": fake.pyint(),
            "spectator_host_session_id": uuid.uuid4(),
        },
        "expires_at": fake.date_time(),
        "created_at": fake.date_time(),
        "updated_at": fake.date_time(),
    }


def fake_account() -> "Account":
    return {
        "account_id": fake.pyint(),
        "username": fake.user_name(),
        "email_address": fake.email(),
        "privileges": fake.pyint(),
        "password": fake.password(),
        "country": fake_country(),
        "created_at": fake.date_time(),
        "updated_at": fake.date_time(),
    }
