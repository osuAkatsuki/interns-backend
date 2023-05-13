from typing import TYPE_CHECKING

import aiosu
from aioredlock import Aioredlock
from httpx import AsyncClient

from app import settings
from app.adapters.database import Database
from app.adapters.redis import Redis

if TYPE_CHECKING:
    from types_aiobotocore_s3.client import S3Client

database: Database
redis: Redis
http_client = AsyncClient()
osu_api: aiosu.v2.Client
s3_client: "S3Client"
redlock = Aioredlock(
    redis_connections=[  # type: ignore
        (settings.REDIS_HOST, settings.REDIS_PORT),
    ],
)
