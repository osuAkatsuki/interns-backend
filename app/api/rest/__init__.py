from fastapi import APIRouter

rest_api_router = APIRouter()

from app.api.rest.v1.accounts.controllers import router as v1_accounts_router
from app.api.rest.v1.scores.controllers import router as v1_scores_router
from app.api.rest.v1.osu_sessions.controllers import router as v1_osu_sessions_router
from app.api.rest.v1.stats.controllers import router as v1_stats_router

rest_api_router.include_router(v1_accounts_router)
rest_api_router.include_router(v1_scores_router)
rest_api_router.include_router(v1_osu_sessions_router)
rest_api_router.include_router(v1_stats_router)
