from fastapi import APIRouter
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.responses import Success
from app.api.rest.v1.accounts.models import Account
from app.errors import ServiceError
from app.services import accounts

router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case ServiceError.ACCOUNTS_COUNTRY_INVALID:
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        case ServiceError.ACCOUNTS_EMAIL_ADDRESS_INVALID:
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        case ServiceError.ACCOUNTS_PASSWORD_INVALID:
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        case ServiceError.ACCOUNTS_USERNAME_INVALID:
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        case ServiceError.INTERNAL_SERVER_ERROR:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case ServiceError.ACCOUNTS_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case _:
            logger.warning(
                "Unhandled error code in accounts rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


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
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch accounts",
            status_code=status_code,
        )

    total = await accounts.fetch_total_count(privileges=privileges)
    if isinstance(total, ServiceError):
        status_code = determine_status_code(total)
        return responses.failure(
            error=total,
            message="Failed to fetch accounts",
            status_code=status_code,
        )

    resp = [Account.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


@router.get("/v1/accounts/{account_id}")
async def fetch_one(account_id: int) -> Success[Account]:
    data = await accounts.fetch_by_account_id(account_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch account",
            status_code=status_code,
        )

    resp = Account.parse_obj(data)
    return responses.success(content=resp)
