#!/usr/bin/env python3
import aiosu
from aiobotocore.session import get_session
from fastapi import FastAPI

from server import clients
from server import logger
from server import settings
from server.adapters import database
from server.adapters import redis
from server.api.osu.bancho import bancho_router
from server.api.osu.web import osu_web_router

app = FastAPI()

# osu web hosts
app.host("osu.cmyui.xyz", osu_web_router)

# osu bancho hosts
app.host("c.cmyui.xyz", bancho_router)
app.host("ce.cmyui.xyz", bancho_router)
app.host("c4.cmyui.xyz", bancho_router)
app.host("c5.cmyui.xyz", bancho_router)
app.host("c6.cmyui.xyz", bancho_router)


logger.configure_logging(
    app_env=settings.APP_ENV,
    log_level=settings.APP_LOG_LEVEL,
)


@app.on_event("startup")
async def start_database():
    logger.info("Connecting to database...")
    clients.database = database.Database(
        read_dsn=database.dsn(
            scheme=settings.READ_DB_SCHEME,
            user=settings.READ_DB_USER,
            password=settings.READ_DB_PASS,
            host=settings.READ_DB_HOST,
            port=settings.READ_DB_PORT,
            database=settings.READ_DB_NAME,
        ),
        read_db_ssl=settings.READ_DB_USE_SSL,
        write_dsn=database.dsn(
            scheme=settings.WRITE_DB_SCHEME,
            user=settings.WRITE_DB_USER,
            password=settings.WRITE_DB_PASS,
            host=settings.WRITE_DB_HOST,
            port=settings.WRITE_DB_PORT,
            database=settings.WRITE_DB_NAME,
        ),
        write_db_ssl=settings.WRITE_DB_USE_SSL,
        min_pool_size=settings.DB_POOL_MIN_SIZE,
        max_pool_size=settings.DB_POOL_MAX_SIZE,
    )
    await clients.database.connect()
    logger.info("Connected to database(s)")


@app.on_event("shutdown")
async def shutdown_database():
    logger.info("Closing database connection...")
    await clients.database.disconnect()
    del clients.database
    logger.info("Closed database connection")


@app.on_event("startup")
async def start_redis():
    logger.info("Connecting to Redis...")
    clients.redis = await redis.from_url(
        url=redis.dsn(
            scheme=settings.REDIS_SCHEME,
            passwd=settings.REDIS_PASS,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            database=settings.REDIS_DB,
        ),
    )
    logger.info("Connected to Redis")


@app.on_event("shutdown")
async def shutdown_redis():
    logger.info("Closing Redis connection...")
    await clients.redis.close()
    del clients.redis
    logger.info("Closed Redis connection")


@app.on_event("startup")
async def start_osu_api_client():
    clients.osu_api = aiosu.v2.Client(
        client_id=settings.OSU_API_V2_CLIENT_ID,
        client_secret=settings.OSU_API_V2_CLIENT_SECRET,
        token=aiosu.models.OAuthToken(),
    )


@app.on_event("shutdown")
async def shutdown_osu_api_client():
    await clients.osu_api.close()
    del clients.osu_api


@app.on_event("startup")
async def start_s3_client():
    session = get_session()
    clients.s3_client = await session._create_client(  # type: ignore
        service_name="s3",
        region_name=settings.S3_BUCKET_REGION,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        endpoint_url=settings.S3_ENDPOINT_URL,
    )
    await clients.s3_client.__aenter__()


@app.on_event("shutdown")
async def shutdown_s3_client():
    await clients.s3_client.__aexit__(None, None, None)
    del clients.s3_client
