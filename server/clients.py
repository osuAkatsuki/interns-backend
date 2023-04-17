from databases import Database
from redis.asyncio import Redis
from httpx import AsyncClient

database: Database
redis: Redis
http_client = AsyncClient()
