from typing import Any

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
) -> dict[str, Any]:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO beatmaps (beatmap_id, beatmap_set_id, ranked_status,
                                  beatmap_md5, artist, title, version, creator,
                                  filename, total_length, max_combo,
                                  ranked_status_manually_changed, plays, passes,
                                  mode, bpm, cs, ar, od, hp, star_rating)
            VALUES (:beatmap_id, :beatmap_set_id, :ranked_status,
                    :beatmap_md5, :artist, :title, :version, :creator,
                    :filename, :total_length, :max_combo,
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
    return dict(beatmap._mapping)


async def fetch_many(
    page: int = 1,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    beatmaps = await clients.database.fetch_all(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM beatmaps
            LIMIT :limit
            OFFSET :offset
        """,
        values={
            "limit": page_size,
            "offset": (page - 1) * page_size,
        },
    )

    return [dict(beatmap._mapping) for beatmap in beatmaps]


async def fetch_one(
    beatmap_id: int,
) -> dict[str, Any] | None:
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
    return dict(beatmap._mapping) if beatmap is not None else None
