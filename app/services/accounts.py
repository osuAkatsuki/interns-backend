from datetime import datetime

from app import logger
from app import security
from app import validation
from app._typing import UNSET
from app._typing import Unset
from app.adapters import recaptcha
from app.errors import ServiceError
from app.game_modes import GameMode
from app.repositories import accounts
from app.repositories import stats
from app.repositories.accounts import Account


async def create(
    username: str,
    email_address: str,
    privileges: int,
    password: str,
    country: str,
    recaptcha_token: str,
) -> Account | ServiceError:
    if not await recaptcha.verify_recaptcha(recaptcha_token):
        return ServiceError.RECAPTCHA_VERIFICATION_FAILED

    if not validation.validate_username(username):
        return ServiceError.ACCOUNTS_USERNAME_INVALID

    if not validation.validate_email(email_address):
        return ServiceError.ACCOUNTS_EMAIL_ADDRESS_INVALID

    if not validation.validate_password(password):
        return ServiceError.ACCOUNTS_PASSWORD_INVALID

    country = country.upper()  # "ca" -> "CA"
    if not validation.validate_country(country):
        return ServiceError.ACCOUNTS_COUNTRY_INVALID

    if await accounts.fetch_by_username(username):
        return ServiceError.ACCOUNTS_USERNAME_EXISTS

    if await accounts.fetch_by_email_address(email_address):
        return ServiceError.ACCOUNTS_EMAIL_ADDRESS_EXISTS

    try:
        hashed_password = security.hash_password(password).decode()
        account = await accounts.create(
            username=username,
            email_address=email_address,
            password=hashed_password,
            privileges=privileges,
            country=country,
        )

        for game_mode in [
            GameMode.VN_OSU,
            GameMode.VN_TAIKO,
            GameMode.VN_CATCH,
            GameMode.VN_MANIA,
            GameMode.RX_OSU,
            GameMode.RX_TAIKO,
            GameMode.RX_CATCH,
            GameMode.AP_OSU,
        ]:
            await stats.create(account["account_id"], game_mode)

    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create account", exc_info=exc)
        return ServiceError.INTERNAL_SERVER_ERROR

    logger.info(
        "Successfully created an account",
        account_id=account["account_id"],
        username=username,
        country=country,
    )

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
    username: str | Unset = UNSET,
    email_address: str | Unset = UNSET,
    privileges: int | Unset = UNSET,
    password: str | Unset = UNSET,
    country: str | Unset = UNSET,
    silence_end: datetime | None | Unset = UNSET,
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
