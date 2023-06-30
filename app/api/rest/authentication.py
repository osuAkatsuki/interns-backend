from uuid import UUID

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from app.errors import ServiceError
from app.repositories.web_sessions import WebSession
from app.services import web_sessions

http_scheme = HTTPBearer()


async def http_bearer_authentication(
    http_auth_creds: HTTPAuthorizationCredentials = Depends(http_scheme),
) -> WebSession:
    try:
        bearer_token = UUID(http_auth_creds.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials",
        )

    web_session = await web_sessions.fetch_by_id(web_session_id=bearer_token)
    if isinstance(web_session, ServiceError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    return web_session
