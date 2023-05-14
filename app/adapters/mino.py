import httpx

from app import clients
from app import logger


async def osudirect_search(
    query: str,
    game_mode: int,
    ranked_status: int,
    page: int,
) -> bytes:
    try:
        response = await clients.http_client.get(
            url=f"https://catboy.best/api/search",
            params={
                "q": query,
                "m": game_mode,
                "r": ranked_status,
                "p": page * 100,
                "raw": 1,
            },
        )
    except httpx.NetworkError as exc:
        logger.error(
            "Failed to fetch beatmaps from mino",
            exc_info=exc,
            query=query,
            game_mode=game_mode,
            ranked_status=ranked_status,
            page=page,
        )
        raise  # TODO: handle this with retry logic

    response_data = await response.aread()
    return response_data


async def get_beatmap_set(beatmap_set_id: int) -> bytes:
    try:
        response = await clients.http_client.get(
            url=f"https://catboy.best/api/search/set",
            params={
                "s": beatmap_set_id,
                "raw": 1,
            },
        )
    except httpx.NetworkError as exc:
        logger.error(
            "Failed to fetch beatmap set from mino",
            exc_info=exc,
            beatmap_set_id=beatmap_set_id,
        )
        raise  # TODO: handle this with retry logic

    response_data = await response.aread()
    return response_data


async def get_beatmap(beatmap_id: int) -> bytes:
    try:
        response = await clients.http_client.get(
            url=f"https://catboy.best/api/search/set",
            params={
                "b": beatmap_id,
                "raw": 1,
            },
        )
    except httpx.NetworkError as exc:
        logger.error(
            "Failed to fetch beatmap from mino",
            exc_info=exc,
            beatmap_id=beatmap_id,
        )
        raise  # TODO: handle this with retry logic

    response_data = await response.aread()
    return response_data
