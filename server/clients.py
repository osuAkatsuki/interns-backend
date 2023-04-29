from typing import Any

import aiosu
from databases import Database
from httpx import AsyncClient
from redis.asyncio import Redis
from types_aiobotocore_s3 import Client

database: Database
redis: Redis
http_client = AsyncClient()
osu_api: aiosu.v2.Client
s3_client: Client
