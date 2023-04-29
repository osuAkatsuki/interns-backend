from typing import TYPE_CHECKING

import aiosu
from httpx import AsyncClient
from redis.asyncio import Redis

from server.adapters.database import Database

if TYPE_CHECKING:
    from types_aiobotocore_s3.client import S3Client

database: Database
redis: Redis
http_client = AsyncClient()
osu_api: aiosu.v2.Client
s3_client: "S3Client"
