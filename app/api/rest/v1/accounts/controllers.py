from fastapi import APIRouter
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.accounts.models import Account
from app.errors import ServiceError
from app.services import accounts

router = APIRouter()


@router.get("/v1/accounts")
async def fetch_many(
    privileges: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> Success[list[Account]]:
    data = await accounts.fetch_many(
        privileges=privileges,
        page=page,
        page_size=page_size,
    )
    if isinstance(data, ServiceError):
        match data:
            case ServiceError.ACCOUNTS_COUNTRY_INVALID:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            case ServiceError.ACCOUNTS_EMAIL_ADDRESS_INVALID:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            case ServiceError.ACCOUNTS_PASSWORD_INVALID:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            case ServiceError.ACCOUNTS_USERNAME_INVALID:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            case ServiceError.INTERNAL_SERVER_ERROR:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            case ServiceError.ACCOUNTS_NOT_FOUND:
                status_code = status.HTTP_404_NOT_FOUND
            case _:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                logger.warning(
                    "Unhandled error code in accounts.fetch_many",
                    service_error=data,
                )

        return responses.failure(
            error=data,
            message="Failed to fetch accounts",
            status_code=status_code,
        )

    resp = [Account.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
        },
    )


@router.get("/v1/accounts/{account_id}")
async def fetch_one(account_id: int) -> Success[Account]:
    data = await accounts.fetch_by_account_id(account_id)
    if isinstance(data, ServiceError):
        match data:
            case ServiceError.ACCOUNTS_NOT_FOUND:
                status_code = status.HTTP_404_NOT_FOUND
            case ServiceError.INTERNAL_SERVER_ERROR:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            case _:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                logger.warning(
                    "Unhandled error code in accounts.fetch_one",
                    service_error=data,
                )

        return responses.failure(
            error=data,
            message="Failed to fetch account",
            status_code=status_code,
        )

    resp = Account.parse_obj(data)
    return responses.success(content=resp)
