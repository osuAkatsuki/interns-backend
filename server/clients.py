from databases import Database
from httpx import AsyncClient
from redis.asyncio import Redis

database: Database
redis: Redis
http_client = AsyncClient()
