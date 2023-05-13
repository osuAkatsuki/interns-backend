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

# XXX: app.host is directly from starlette, and is not fully supported
# by the fastapi wrapper; for example, it cannot be found in the docs.
# we will probably want to try finding a better solution for this.

app.host("osu.cmyui.xyz", osu_web_router)

# osu bancho hosts
app.host("c.cmyui.xyz", bancho_router)
app.host("ce.cmyui.xyz", bancho_router)
app.host("c4.cmyui.xyz", bancho_router)
app.host("c5.cmyui.xyz", bancho_router)
app.host("c6.cmyui.xyz", bancho_router)

# rest api hosts
app.host("api.cmyui.xyz", rest_api_router)


@app.on_event("startup")
async def startup() -> None:
    await lifecycle.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await lifecycle.shutdown()