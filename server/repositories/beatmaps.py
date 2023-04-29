from datetime import datetime
from typing import cast
from typing import TypedDict

from server import clients

READ_PARAMS = """\
    beatmap_id,
    beatmap_set_id,
    ranked_status,
    beatmap_md5,
    artist,
    title,
    version,
    creator,
    filename,
    last_update,
    total_length,
    max_combo,
    ranked_status_manually_changed,
    plays,
    passes,
    mode,
    bpm,
    cs,
    ar,
    od,
    hp,
    star_rating
"""


class Beatmap(TypedDict):
    beatmap_id: int
    beatmap_set_id: int
    ranked_status: int
    beatmap_md5: str
    artist: str
    title: str
    version: str
    creator: str
    filename: str
    last_update: datetime
    total_length: int
    max_combo: int
    ranked_status_manually_changed: bool
    plays: int
    passes: int
    mode: int
    bpm: float
    cs: float
    ar: float
    od: float
    hp: float
    star_rating: float


async def create(
    beatmap_id: int,
    beatmap_set_id: int,
    ranked_status: int,
    beatmap_md5: str,
    artist: str,
    title: str,
    version: str,
    creator: str,
    filename: str,
    last_update: datetime,
    total_length: int,
    max_combo: int,
    ranked_status_manually_changed: bool,
    plays: int,
    passes: int,
    mode: int,
    bpm: float,
    cs: float,
    ar: float,
    od: float,
    hp: float,
    star_rating: float,
) -> Beatmap:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO beatmaps (beatmap_id, beatmap_set_id, ranked_status,
                                  beatmap_md5, artist, title, version, creator,
                                  filename, last_update, total_length, max_combo,
                                  ranked_status_manually_changed, plays, passes,
                                  mode, bpm, cs, ar, od, hp, star_rating)
            VALUES (:beatmap_id, :beatmap_set_id, :ranked_status,
                    :beatmap_md5, :artist, :title, :version, :creator,
                    :filename, :last_update, :total_length, :max_combo,
                    :ranked_status_manually_changed, :plays, :passes,
                    :mode, :bpm, :cs, :ar, :od, :hp, :star_rating)
            RETURNING {READ_PARAMS}
        """,
        values={
            "beatmap_id": beatmap_id,
            "beatmap_set_id": beatmap_set_id,
            "ranked_status": ranked_status,
            "beatmap_md5": beatmap_md5,
            "artist": artist,
            "title": title,
            "version": version,
            "creator": creator,
            "filename": filename,
            "last_update": last_update,
            "total_length": total_length,
            "max_combo": max_combo,
            "ranked_status_manually_changed": ranked_status_manually_changed,
            "plays": plays,
            "passes": passes,
            "mode": mode,
            "bpm": bpm,
            "cs": cs,
            "ar": ar,
            "od": od,
            "hp": hp,
            "star_rating": star_rating,
        },
    )

    assert beatmap is not None
    return cast(Beatmap, dict(beatmap._mapping))


async def fetch_many(
    page: int | None = None,
    page_size: int | None = None,
) -> list[Beatmap]:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM beatmaps
    """
    values = {}
    if page is not None and page_size is not None:
        query += """\
            LIMIT :limit
            OFFSET :offset
        """
        values["limit"] = page
        values["offset"] = (page - 1) * page_size

    beatmaps = await clients.database.fetch_all(query, values)
    return [cast(Beatmap, dict(beatmap._mapping)) for beatmap in beatmaps]


async def fetch_one_by_id(beatmap_id: int) -> Beatmap | None:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM beatmaps
            WHERE beatmap_id = :beatmap_id
        """,
        values={
            "beatmap_id": beatmap_id,
        },
    )
    return cast(Beatmap, dict(beatmap._mapping)) if beatmap is not None else None


async def fetch_one_by_md5(beatmap_md5: str) -> Beatmap | None:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM beatmaps
            WHERE beatmap_md5 = :beatmap_md5
        """,
        values={
            "beatmap_md5": beatmap_md5,
        },
    )
    return cast(Beatmap, dict(beatmap._mapping)) if beatmap is not None else None
