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
    star_rating,
    updated_at
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
    updated_at: datetime,
) -> Beatmap:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO beatmaps (beatmap_id, beatmap_set_id, ranked_status,
                                  beatmap_md5, artist, title, version, creator,
                                  filename, total_length, max_combo,
                                  ranked_status_manually_changed, plays, passes,
                                  mode, bpm, cs, ar, od, hp, star_rating, updated_at)
            VALUES (:beatmap_id, :beatmap_set_id, :ranked_status,
                    :beatmap_md5, :artist, :title, :version, :creator,
                    :filename, :total_length, :max_combo,
                    :ranked_status_manually_changed, :plays, :passes,
                    :mode, :bpm, :cs, :ar, :od, :hp, :star_rating, :updated_at)
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
            "updated_at": updated_at,
        },
    )

    assert beatmap is not None
    return cast(Beatmap, beatmap)


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
    return [cast(Beatmap, beatmap) for beatmap in beatmaps]


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
    return cast(Beatmap, beatmap) if beatmap is not None else None


async def partial_update(
    beatmap_id: int,
    ranked_status: int | None = None,
    beatmap_md5: str | None = None,
    artist: str | None = None,
    title: str | None = None,
    version: str | None = None,
    creator: str | None = None,
    filename: str | None = None,
    last_update: datetime | None = None,
    total_length: int | None = None,
    max_combo: int | None = None,
    ranked_status_manually_changed: bool | None = None,
    plays: int | None = None,
    passes: int | None = None,
    mode: int | None = None,
    bpm: float | None = None,
    cs: float | None = None,
    ar: float | None = None,
    od: float | None = None,
    hp: float | None = None,
    star_rating: float | None = None,
) -> Beatmap | None:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            UPDATE beatmaps
            SET ranked_status = COALESCE(:ranked_status, ranked_status),
                beatmap_md5 = COALESCE(:beatmap_md5, beatmap_md5),
                artist = COALESCE(:artist, artist),
                title = COALESCE(:title, title),
                version = COALESCE(:version, version),
                creator = COALESCE(:creator, creator),
                filename = COALESCE(:filename, filename),
                last_update = COALESCE(:last_update, last_update),
                total_length = COALESCE(:total_length, total_length),
                max_combo = COALESCE(:max_combo, max_combo),
                ranked_status_manually_changed = COALESCE(:ranked_status_manually_changed, ranked_status_manually_changed),
                plays = COALESCE(:plays, plays),
                passes = COALESCE(:passes, passes),
                mode = COALESCE(:mode, mode),
                bpm = COALESCE(:bpm, bpm),
                cs = COALESCE(:cs, cs),
                ar = COALESCE(:ar, ar),
                od = COALESCE(:od, od),
                hp = COALESCE(:hp, hp),
                star_rating = COALESCE(:star_rating, star_rating)
            WHERE beatmap_id = :beatmap_id
            RETURNING {READ_PARAMS}
        """,
        values={
            "beatmap_id": beatmap_id,
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
    return cast(Beatmap, beatmap) if beatmap is not None else None


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
    return cast(Beatmap, beatmap) if beatmap is not None else None
