from datetime import datetime

from app import logger
from app import validation
from app.errors import ServiceError
from app.repositories import accounts
from app.repositories.accounts import Account
from app.undefined import Undefined, UndefinedType

async def create(
    username: str,
    email_address: str,
    privileges: int,
    password: str,
    country: str,
) -> Account | ServiceError:
    if not validation.validate_username(username):
        return ServiceError.ACCOUNTS_USERNAME_INVALID

    if not validation.validate_email(email_address):
        return ServiceError.ACCOUNTS_EMAIL_ADDRESS_INVALID

    if not validation.validate_password(password):
        return ServiceError.ACCOUNTS_PASSWORD_INVALID

    if not validation.validate_country(country):
        return ServiceError.ACCOUNTS_COUNTRY_INVALID

    try:
        account = await accounts.create(
            username=username,
            email_address=email_address,
            password=password,
            privileges=privileges,
            country=country,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create account", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return account


async def fetch_many(
    privileges: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> list[Account] | ServiceError:
    try:
        _accounts = await accounts.fetch_many(
            privileges=privileges,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch accounts", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return _accounts


async def fetch_total_count(
    privileges: int | None = None,
) -> int | ServiceError:
    try:
        count = await accounts.fetch_total_count(
            privileges=privileges,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch accounts", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    return count


async def fetch_by_account_id(account_id: int) -> Account | ServiceError:
    try:
        account = await accounts.fetch_by_account_id(account_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch account", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if account is None:
        return ServiceError.ACCOUNTS_NOT_FOUND

    return account


async def fetch_by_username(username: str) -> Account | ServiceError:
    try:
        account = await accounts.fetch_by_username(username)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch account", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if account is None:
        return ServiceError.ACCOUNTS_NOT_FOUND

    return account


async def partial_update(
    account_id: int,
    username: str | UndefinedType = Undefined,
    email_address: str | UndefinedType = Undefined,
    privileges: int | UndefinedType = Undefined,
    password: str | UndefinedType = Undefined,
    country: str | UndefinedType = Undefined,
    silence_end: datetime | None | UndefinedType = Undefined,
) -> Account | ServiceError:
    try:
        account = await accounts.partial_update(
            account_id,
            username,
            email_address,
            privileges,
            password,
            country,
            silence_end,
        )
    except Exception as exc:
        logger.error("Failed to update account", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    if not account:
            return ServiceError.ACCOUNTS_NOT_FOUND

    return account