from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from app import logger
from app.api.rest import responses
from app.api.rest.authentication import http_bearer_authentication
from app.api.rest.responses import Success
from app.api.rest.v1.web_sessions.models import APIv1LoginCredentials
from app.api.rest.v1.web_sessions.models import APIv1WebSession
from app.errors import ServiceError
from app.repositories.web_sessions import WebSession
from app.services import web_sessions


router = APIRouter()


def determine_status_code(error: ServiceError) -> int:
    match error:
        case ServiceError.WEB_SESSIONS_NOT_FOUND:
            return status.HTTP_404_NOT_FOUND
        case ServiceError.CREDENTIALS_NOT_FOUND:
            return status.HTTP_401_UNAUTHORIZED
        case ServiceError.CREDENTIALS_INCORRECT:
            return status.HTTP_401_UNAUTHORIZED
        case (ServiceError.INTERNAL_SERVER_ERROR):
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        case ServiceError.RECAPTCHA_VERIFICATION_FAILED:
            return status.HTTP_400_BAD_REQUEST
        case _:
            logger.warning(
                "Unhandled error code in web sessions rest api controller",
                service_error=error,
            )
            return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post("/v1/web_sessions")
async def authenticate(credentials: APIv1LoginCredentials) -> Success[APIv1WebSession]:
    data = await web_sessions.authenticate(
        username=credentials.username,
        password=credentials.password,
        recaptcha_token=credentials.recaptcha_token,
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to login",
            status_code=status_code,
        )

    resp = APIv1WebSession.parse_obj(data)
    return responses.success(content=resp)


@router.get("/v1/web_sessions")
async def fetch_many(
    page: int = 1,
    page_size: int = 50,
) -> Success[list[APIv1WebSession]]:
    data = await web_sessions.fetch_many(
        page=page,
        page_size=page_size,
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch web sessions",
            status_code=status_code,
        )

    total = await web_sessions.fetch_total_count()
    if isinstance(total, ServiceError):
        status_code = determine_status_code(total)
        return responses.failure(
            error=total,
            message="Failed to fetch web sessions",
            status_code=status_code,
        )

    resp = [APIv1WebSession.parse_obj(rec) for rec in data]
    return responses.success(
        content=resp,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
        },
    )


@router.get("/v1/web_sessions/{web_session_id}")
async def fetch_one(web_session_id: UUID) -> Success[APIv1WebSession]:
    data = await web_sessions.fetch_by_id(web_session_id)
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to fetch web session",
            status_code=status_code,
        )

    resp = APIv1WebSession.parse_obj(data)
    return responses.success(content=resp)


@router.delete("/v1/web_sessions")
async def delete_one(
    current_web_session: WebSession = Depends(http_bearer_authentication),
) -> Success[None]:
    data = await web_sessions.delete_by_id(
        web_session_id=current_web_session["web_session_id"],
    )
    if isinstance(data, ServiceError):
        status_code = determine_status_code(data)
        return responses.failure(
            error=data,
            message="Failed to delete web sessions",
            status_code=status_code,
        )

    return responses.success(content=None)
