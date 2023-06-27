from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients
from app.typing import UNSET
from app.typing import Unset

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
    bancho_ranked_status,
    bancho_updated_at,
    created_at,
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
    bancho_ranked_status: int
    bancho_updated_at: datetime
    created_at: datetime
    updated_at: datetime


class BeatmapUpdateFields(TypedDict, total=False):
    ranked_status: int | Unset
    beatmap_md5: str | Unset
    artist: str | Unset
    title: str | Unset
    version: str | Unset
    creator: str | Unset
    filename: str | Unset
    total_length: int | Unset
    max_combo: int | Unset
    ranked_status_manually_changed: bool | Unset
    plays: int | Unset
    passes: int | Unset
    mode: int | Unset
    bpm: float | Unset
    cs: float | Unset
    ar: float | Unset
    od: float | Unset
    hp: float | Unset
    star_rating: float | Unset
    bancho_ranked_status: int | Unset
    bancho_updated_at: datetime | Unset
    username: str
    email_address: str
    privileges: int
    password: str
    country: str
    silence_end: datetime | None


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
    bancho_ranked_status: int,
    bancho_updated_at: datetime,
) -> Beatmap:
    beatmap = await clients.database.fetch_one(
        query=f"""\
            INSERT INTO beatmaps (beatmap_id, beatmap_set_id, ranked_status,
                                  beatmap_md5, artist, title, version, creator,
                                  filename, total_length, max_combo,
                                  ranked_status_manually_changed, plays, passes,
                                  mode, bpm, cs, ar, od, hp, star_rating,
                                  bancho_ranked_status, bancho_updated_at)
            VALUES (:beatmap_id, :beatmap_set_id, :ranked_status,
                    :beatmap_md5, :artist, :title, :version, :creator,
                    :filename, :total_length, :max_combo,
                    :ranked_status_manually_changed, :plays, :passes,
                    :mode, :bpm, :cs, :ar, :od, :hp, :star_rating,
                    :bancho_ranked_status, :bancho_updated_at)
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
            "bancho_ranked_status": bancho_ranked_status,
            "bancho_updated_at": bancho_updated_at,
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
    return cast(list[Beatmap], beatmaps)


async def fetch_one(
    beatmap_md5: str | None = None,
    file_name: str | None = None,
    beatmap_id: int | None = None,
) -> Beatmap | None:
    assert (beatmap_md5, file_name, beatmap_id).count(None) == 2

    beatmap = await clients.database.fetch_one(
        query=f"""\
            SELECT {READ_PARAMS}
            FROM beatmaps
            WHERE beatmap_md5 = COALESCE(:beatmap_md5, beatmap_md5)
            AND filename = COALESCE(:filename, filename)
            AND beatmap_id = COALESCE(:beatmap_id, beatmap_id)
        """,
        values={
            "beatmap_md5": beatmap_md5,
            "filename": file_name,
            "beatmap_id": beatmap_id,
        },
    )
    return cast(Beatmap, beatmap) if beatmap is not None else None


async def partial_update(
    beatmap_id: int,
    ranked_status: int | Unset = UNSET,
    beatmap_md5: str | Unset = UNSET,
    artist: str | Unset = UNSET,
    title: str | Unset = UNSET,
    version: str | Unset = UNSET,
    creator: str | Unset = UNSET,
    filename: str | Unset = UNSET,
    total_length: int | Unset = UNSET,
    max_combo: int | Unset = UNSET,
    ranked_status_manually_changed: bool | Unset = UNSET,
    plays: int | Unset = UNSET,
    passes: int | Unset = UNSET,
    mode: int | Unset = UNSET,
    bpm: float | Unset = UNSET,
    cs: float | Unset = UNSET,
    ar: float | Unset = UNSET,
    od: float | Unset = UNSET,
    hp: float | Unset = UNSET,
    star_rating: float | Unset = UNSET,
    bancho_ranked_status: int | Unset = UNSET,
    bancho_updated_at: datetime | Unset = UNSET,
) -> Beatmap | None:
    update_fields: BeatmapUpdateFields = {}
    if not isinstance(ranked_status, Unset):
        update_fields["ranked_status"] = ranked_status
    if not isinstance(beatmap_md5, Unset):
        update_fields["beatmap_md5"] = beatmap_md5
    if not isinstance(artist, Unset):
        update_fields["artist"] = artist
    if not isinstance(title, Unset):
        update_fields["title"] = title
    if not isinstance(version, Unset):
        update_fields["version"] = version
    if not isinstance(creator, Unset):
        update_fields["creator"] = creator
    if not isinstance(filename, Unset):
        update_fields["filename"] = filename
    if not isinstance(total_length, Unset):
        update_fields["total_length"] = total_length
    if not isinstance(max_combo, Unset):
        update_fields["max_combo"] = max_combo
    if not isinstance(ranked_status_manually_changed, Unset):
        update_fields["ranked_status_manually_changed"] = ranked_status_manually_changed
    if not isinstance(plays, Unset):
        update_fields["plays"] = plays
    if not isinstance(passes, Unset):
        update_fields["passes"] = passes
    if not isinstance(mode, Unset):
        update_fields["mode"] = mode
    if not isinstance(bpm, Unset):
        update_fields["bpm"] = bpm
    if not isinstance(cs, Unset):
        update_fields["cs"] = cs
    if not isinstance(ar, Unset):
        update_fields["ar"] = ar
    if not isinstance(od, Unset):
        update_fields["od"] = od
    if not isinstance(hp, Unset):
        update_fields["hp"] = hp
    if not isinstance(star_rating, Unset):
        update_fields["star_rating"] = star_rating
    if not isinstance(bancho_ranked_status, Unset):
        update_fields["bancho_ranked_status"] = bancho_ranked_status
    if not isinstance(bancho_updated_at, Unset):
        update_fields["bancho_updated_at"] = bancho_updated_at

    query = f"""\
        UPDATE beatmaps
           SET {", ".join(f"{key} = :{key}" for key in update_fields)},
               updated_at = NOW()
        WHERE beatmap_id = :beatmap_id
        RETURNING {READ_PARAMS}
    """
    values = {"beatmap_id": beatmap_id} | update_fields
    beatmap = await clients.database.fetch_one(query, values)
    return cast(Beatmap, beatmap) if beatmap is not None else None
