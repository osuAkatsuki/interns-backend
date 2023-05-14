import base64
import ssl

import aiosu
from aiobotocore.session import get_session

from app import clients
from app import logger
from app import settings
from app.adapters import database
from app.adapters import redis


async def _start_database():
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
        read_db_ssl=(
            ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH,
                cadata=base64.b64decode(
                    settings.READ_DB_CA_CERTIFICATE_BASE64
                ).decode(),
            )
            if settings.READ_DB_USE_SSL
            else False
        ),
        write_dsn=database.dsn(
            scheme=settings.WRITE_DB_SCHEME,
            user=settings.WRITE_DB_USER,
            password=settings.WRITE_DB_PASS,
            host=settings.WRITE_DB_HOST,
            port=settings.WRITE_DB_PORT,
            database=settings.WRITE_DB_NAME,
        ),
        write_db_ssl=(
            ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH,
                cadata=base64.b64decode(
                    settings.WRITE_DB_CA_CERTIFICATE_BASE64
                ).decode(),
            )
            if settings.WRITE_DB_USE_SSL
            else False
        ),
        min_pool_size=settings.DB_POOL_MIN_SIZE,
        max_pool_size=settings.DB_POOL_MAX_SIZE,
    )
    await clients.database.connect()
    logger.info("Connected to database(s)")


async def _shutdown_database():
    logger.info("Closing database connection...")
    await clients.database.disconnect()
    del clients.database
    logger.info("Closed database connection")


async def _start_redis():
    logger.info("Connecting to Redis...")
    clients.redis = await redis.from_url(
        url=redis.dsn(
            scheme=settings.REDIS_SCHEME,
            username=settings.REDIS_USER,
            password=settings.REDIS_PASS,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            database=settings.REDIS_DB,
        ),
    )
    logger.info("Connected to Redis")


async def _shutdown_redis():
    logger.info("Closing Redis connection...")
    await clients.redis.close()
    del clients.redis
    logger.info("Closed Redis connection")


async def _start_osu_api_client():
    clients.osu_api = aiosu.v2.Client(
        client_id=settings.OSU_API_V2_CLIENT_ID,
        client_secret=settings.OSU_API_V2_CLIENT_SECRET,
        token=aiosu.models.OAuthToken(),
    )


async def _shutdown_osu_api_client():
    await clients.osu_api.close()
    del clients.osu_api


async def _start_s3_client():
    session = get_session()
    clients.s3_client = await session._create_client(  # type: ignore
        service_name="s3",
        region_name=settings.S3_BUCKET_REGION,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        endpoint_url=settings.S3_ENDPOINT_URL,
    )
    await clients.s3_client.__aenter__()


async def _shutdown_s3_client():
    await clients.s3_client.__aexit__(None, None, None)
    del clients.s3_client


async def start():
    await _start_database()
    await _start_redis()
    await _start_osu_api_client()
    await _start_s3_client()


async def shutdown():
    await _shutdown_s3_client()
    await _shutdown_osu_api_client()
    await _shutdown_redis()
    await _shutdown_database()
