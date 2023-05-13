import redis.asyncio
from redis.asyncio import Redis as _Redis


class Redis(_Redis):
    ...


def dsn(
    scheme: str,
    host: str,
    port: int,
    passwd: str,
    database: int,
) -> str:
    # TODO: *optional* passwd support?
    # TODO: optional user support?
    return f"{scheme}://{passwd}@{host}:{port}/{database}?password={passwd}"


async def from_url(url: str) -> Redis:
    return await redis.asyncio.from_url(url)
