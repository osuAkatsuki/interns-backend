from fastapi import APIRouter

rest_api_router = APIRouter()

from app.api.rest.v1.accounts.controllers import router as v1_accounts_router

rest_api_router.include_router(v1_accounts_router)