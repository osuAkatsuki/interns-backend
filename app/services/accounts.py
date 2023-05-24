from app import logger
from app import validation
from app.errors import ServiceError
from app.repositories import accounts
from app.repositories.accounts import Account


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


# TODO: PARTIAL UPDATE w/ silence end integration
async def partial_update(
    account_id: int,
    username: str | None,
    email_address: str | None,
    privileges: int | None,
    password: str | None,
    country: str | None,
) -> Account | ServiceError:
    ...
