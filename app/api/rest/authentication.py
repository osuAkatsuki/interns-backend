from uuid import UUID

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from app.services import web_sessions

http_scheme = HTTPBearer()


async def authenticate(
    http_auth_creds: HTTPAuthorizationCredentials = Depends(http_scheme),
):
    try:
        bearer_token = UUID(http_auth_creds.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials",
        )

    web_session = await web_sessions.fetch_by_id(web_session_id=bearer_token)
    if web_session is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    return web_session
