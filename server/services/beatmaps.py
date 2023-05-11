from datetime import datetime
from datetime import timedelta

from server.adapters import osu_api_v2
from server.errors import ServiceError
from server.repositories import beatmaps
from server.repositories.beatmaps import Beatmap
from server.repositories.beatmaps import BeatmapRankedStatus


def _create_beatmap_filename(
    artist: str,
    title: str,
    version: str,
    creator: str,
) -> str:
    return f"{artist} - {title} ({creator}) [{version}].osu"


def _transform_to_internal_model(osu_api_beatmap: osu_api_v2.Beatmap) -> Beatmap:
    assert osu_api_beatmap.beatmap_md5 is not None
    assert osu_api_beatmap.last_updated is not None  # TODO?
    assert osu_api_beatmap.beatmapset is not None

    return {
        "beatmap_id": osu_api_beatmap.beatmap_id,
        "beatmap_set_id": osu_api_beatmap.beatmap_set_id,
        "ranked_status": osu_api_beatmap.ranked_status,
        "beatmap_md5": osu_api_beatmap.beatmap_md5,
        "artist": osu_api_beatmap.beatmapset.artist,
        "title": osu_api_beatmap.beatmapset.title,
        "version": osu_api_beatmap.version,
        "creator": osu_api_beatmap.beatmapset.creator_name,
        "filename": _create_beatmap_filename(
            artist=osu_api_beatmap.beatmapset.artist,
            title=osu_api_beatmap.beatmapset.title,
            version=osu_api_beatmap.version,
            creator=osu_api_beatmap.beatmapset.creator_name,
        ),
        "total_length": osu_api_beatmap.total_length,
        "max_combo": osu_api_beatmap.max_combo or 0,
        "ranked_status_manually_changed": False,  # manually ranked
        "plays": 0,  # plays
        "passes": 0,  # passes
        "mode": osu_api_beatmap.game_mode,
        "bpm": osu_api_beatmap.bpm or 0,
        "cs": osu_api_beatmap.cs or 0,
        "ar": osu_api_beatmap.ar or 0,
        "od": osu_api_beatmap.od or 0,
        "hp": osu_api_beatmap.hp or 0,
        "star_rating": osu_api_beatmap.star_rating,
        "updated_at": osu_api_beatmap.last_updated or datetime.now(),
    }


def _should_get_updates(beatmap: Beatmap) -> bool:
    match beatmap["ranked_status"]:
        case BeatmapRankedStatus.GRAVEYARD:
            # TODO: scale this with time since last beatmap update
            update_interval = timedelta(days=1)
        case BeatmapRankedStatus.QUALIFIED:
            update_interval = timedelta(minutes=5)
        case BeatmapRankedStatus.PENDING:
            update_interval = timedelta(minutes=10)
        case BeatmapRankedStatus.WIP:
            update_interval = timedelta(minutes=5)
        case BeatmapRankedStatus.LOVED:
            # loved maps can *technically* be updated
            update_interval = timedelta(days=1)
        case BeatmapRankedStatus.RANKED | BeatmapRankedStatus.APPROVED:
            # in very rare cases, the osu! team has updated ranked/appvoed maps
            # this is usually done to remove things like inappropriate content
            update_interval = timedelta(days=1)
        case _:
            raise NotImplementedError(
                f"Unknown ranked status: {beatmap['ranked_status']}"
            )

    return beatmap["updated_at"] <= (datetime.now() - update_interval)


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
) -> Beatmap | ServiceError:
    beatmap = await beatmaps.create(
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
        updated_at,
    )
    if beatmap is None:
        return ServiceError.BEATMAPS_CREATE_FAILED

    return beatmap


async def fetch_many(
    page: int | None = None,
    page_size: int | None = None,
) -> list[Beatmap]:
    return await beatmaps.fetch_many(page, page_size)


async def fetch_one(
    beatmap_md5: str | None = None,
    file_name: str | None = None,
    beatmap_id: int | None = None,
) -> Beatmap | ServiceError:
    beatmap = await beatmaps.fetch_one(
        beatmap_md5=beatmap_md5,
        file_name=file_name,
        beatmap_id=beatmap_id,
    )

    # since we are mirroring beatmap data from osu!api v2,
    # we need to check if we need to update the beatmap

    # we will also JIT create the beatmap if it doesn't exist yet

    # we don't have the map persisted yet
    if not beatmap:
        osu_api_beatmap = await osu_api_v2.lookup_beatmap(
            beatmap_md5=beatmap_md5,
            file_name=file_name,
            beatmap_id=beatmap_id,
        )
        if not osu_api_beatmap:
            return ServiceError.BEATMAPS_NOT_FOUND

        beatmap = _transform_to_internal_model(osu_api_beatmap)
        await beatmaps.create(**beatmap)

    # we have this map, but it might be outdated
    elif _should_get_updates(beatmap):
        osu_api_beatmap = await osu_api_v2.lookup_beatmap(
            beatmap_md5=beatmap_md5,
            file_name=file_name,
            beatmap_id=beatmap_id,
        )
        assert osu_api_beatmap is not None

        new_beatmap = _transform_to_internal_model(osu_api_beatmap)

        # keep changes that are manually set by the beatmap nomination team
        if beatmap["ranked_status_manually_changed"]:
            new_beatmap["ranked_status"] = beatmap["ranked_status"]
            new_beatmap["ranked_status_manually_changed"] = True

        # persist changes
        await beatmaps.partial_update(
            new_beatmap["beatmap_id"],
            new_beatmap["ranked_status"],
            new_beatmap["beatmap_md5"],
            new_beatmap["artist"],
            new_beatmap["title"],
            new_beatmap["version"],
            new_beatmap["creator"],
            new_beatmap["filename"],
            new_beatmap["total_length"],
            new_beatmap["max_combo"],
            new_beatmap["ranked_status_manually_changed"],
            new_beatmap["plays"],
            new_beatmap["passes"],
            new_beatmap["mode"],
            new_beatmap["bpm"],
            new_beatmap["cs"],
            new_beatmap["ar"],
            new_beatmap["od"],
            new_beatmap["hp"],
            new_beatmap["star_rating"],
            new_beatmap["updated_at"],
        )
        beatmap = new_beatmap

    return beatmap


async def partial_update(
    beatmap_id: int,
    ranked_status: int | None = None,
    beatmap_md5: str | None = None,
    artist: str | None = None,
    title: str | None = None,
    version: str | None = None,
    creator: str | None = None,
    filename: str | None = None,
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
    updated_at: datetime | None = None,
) -> Beatmap | ServiceError:
    beatmap = await beatmaps.partial_update(
        beatmap_id,
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
        updated_at,
    )
    if beatmap is None:
        return ServiceError.BEATMAPS_NOT_FOUND

    return beatmap
