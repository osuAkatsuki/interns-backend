import aiosu
from databases import Database
from httpx import AsyncClient
from redis.asyncio import Redis
from typing import Any

database: Database
redis: Redis
http_client = AsyncClient()
osu_api: aiosu.v2.Client
s3_client: Any
