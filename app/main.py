#!/usr/bin/env python3
from fastapi import FastAPI

from app import lifecycle
from app import logger
from app import settings
from app.api.osu.bancho import bancho_router
from app.api.osu.web import osu_web_router
from app.api.rest import rest_api_router

logger.configure_logging(
    app_env=settings.APP_ENV,
    log_level=settings.APP_LOG_LEVEL,
)

app = FastAPI()

app.include_router(osu_web_router)
app.include_router(bancho_router)

# rest api hosts
app.host("api.cmyui.xyz", rest_api_router)


@app.on_event("startup")
async def startup() -> None:
    await lifecycle.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await lifecycle.shutdown()
