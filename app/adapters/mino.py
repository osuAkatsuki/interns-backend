from datetime import datetime

import httpx
from pydantic import BaseModel

from app import clients
from app import logger


class Beatmap(BaseModel):
    FileMD5: str
    TotalLength: int
    Playcount: int
    Mode: int
    HP: int
    Ranked: int
    MaxCombo: int
    ParentSetID: int
    CS: int
    AR: int
    OD: int
    BeatmapID: int
    HitLength: int
    DifficultyRating: int
    Passcount: int
    DiffName: str
    BPM: int


class BeatmapSet(BaseModel):
    SetID: int
    RankedStatus: int
    ChildrenBeatmaps: list[Beatmap]
    ApprovedDate: datetime
    LastUpdate: datetime
    LastChecked: datetime
    Artist: str
    Title: str
    Creator: str
    CreatorID: int
    Source: str
    Tags: str
    HasVideo: int  # bool
    Favourites: int


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


async def get_beatmap_set(beatmap_set_id: int) -> BeatmapSet | None:
    try:
        response = await clients.http_client.get(
            url=f"https://catboy.best/s/{beatmap_set_id}",
        )
    except httpx.NetworkError as exc:
        logger.error(
            "Failed to fetch beatmap set from mino",
            exc_info=exc,
            beatmap_set_id=beatmap_set_id,
        )
        raise  # TODO: handle this with retry logic

    response_data = await response.json()
    if response_data["error"]:
        return None

    return BeatmapSet(**response_data)


async def get_beatmap(beatmap_id: int) -> Beatmap | None:
    try:
        response = await clients.http_client.get(
            url=f"https://catboy.best/b/{beatmap_id}",
        )
    except httpx.NetworkError as exc:
        logger.error(
            "Failed to fetch beatmap from mino",
            exc_info=exc,
            beatmap_id=beatmap_id,
        )
        raise  # TODO: handle this with retry logic

    response_data = await response.json()
    if "error" in response_data:
        return None

    return Beatmap(**response_data)
