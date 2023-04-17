from typing import Any

import validation
from errors import ServiceError


async def create(
    username: str,
    email_address: str,
    privileges: int,
    password: str,
    country: str,
) -> dict[str, Any] | ServiceError:
    if not validation.validate_username(username):
        return ServiceError.ACCOUNTS_USERNAME_INVALID

    if not validation.email_validator(email_address):
        return ServiceError.ACCOUNTS_EMAIL_ADDRESS_INVALID

    if not validation.validate_password(password):
        return ServiceError.ACCOUNTS_PASSWORD_INVALID

    # TODO: Ask Cmyui if there is service error for privlidegs
