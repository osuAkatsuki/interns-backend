import redis.asyncio
from redis.asyncio import Redis as _Redis


class Redis(_Redis):
    ...


def dsn(
    scheme: str,
    username: str | None,
    host: str,
    port: int,
    password: str,
    database: int,
) -> str:
    # TODO: *optional* passwd support?
    if username is not None:
        return f"{scheme}://{username}:{password}@{host}:{port}/{database}"
    else:
        return f"{scheme}://{password}@{host}:{port}/{database}"


async def from_url(url: str) -> Redis:
    return await redis.asyncio.from_url(url)
