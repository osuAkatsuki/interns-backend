from datetime import datetime
from enum import Enum

import aiosu
import httpx
from pydantic import BaseModel

from app import clients
from app import logger


# TODO: implement retry logic


class BeatmapRankedStatus(Enum):
    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


class BeatmapFailtimes(BaseModel):
    exit: list[int] | None
    fail: list[int] | None


class BeatmapCovers(BaseModel):
    cover: str
    card: str
    list: str
    slimcover: str
    cover_2_x: str | None = None
    card_2_x: str | None = None
    list_2_x: str | None = None
    slimcover_2_x: str | None = None


class BeatmapHype(BaseModel):
    current: int
    required: int


class BeatmapAvailability(BaseModel):
    more_information: str | None
    download_disabled: bool | None


class BeatmapNominations(BaseModel):
    current: int | None
    required: int | None


class BeatmapSet(BaseModel):
    beatmap_set_id: int
    artist: str
    artist_unicode: str
    covers: BeatmapCovers
    creator_name: str
    favourite_count: int
    play_count: int
    preview_url: str
    source: str
    status: BeatmapRankedStatus
    title: str
    title_unicode: str
    creator_id: int
    video: bool
    nsfw: bool | None
    hype: BeatmapHype | None
    availability: BeatmapAvailability | None
    bpm: float | None
    can_be_hyped: bool | None
    discussion_enabled: bool | None
    discussion_locked: bool | None
    is_scoreable: bool | None
    last_updated: datetime | None
    legacy_thread_url: str | None
    nominations_summary: BeatmapNominations | None
    ranked_date: datetime | None
    storyboard: bool | None
    submitted_date: datetime | None
    tags: str | None
    ratings: list[int] | None
    has_favourited: bool | None
    beatmaps: list["Beatmap"] | None


class Beatmap(BaseModel):
    beatmap_id: int
    beatmap_url: str
    game_mode: int
    beatmap_set_id: int
    star_rating: float
    ranked_status: int
    total_length: int
    creator_id: int
    version: str
    od: float | None
    ar: float | None
    cs: float | None
    hp: float | None
    bpm: float | None
    convert: bool | None
    num_circles: int | None
    num_sliders: int | None
    num_spinners: int | None
    deleted_at: datetime | None
    hit_length: int | None
    is_scoreable: bool | None
    last_updated: datetime | None
    passcount: int | None
    play_count: int | None = None
    beatmap_md5: str | None
    max_combo: int | None
    beatmapset: BeatmapSet | None
    failtimes: BeatmapFailtimes | None


BeatmapSet.update_forward_refs()  # fix circular reference for runtime


def beatmap_from_aiosu(aiosu_beatmap: aiosu.models.Beatmap) -> Beatmap:
    aiosu_beatmapset = aiosu_beatmap.beatmapset
    assert aiosu_beatmapset is not None

    return Beatmap(
        beatmap_id=aiosu_beatmap.id,
        beatmap_url=aiosu_beatmap.url,
        game_mode=aiosu_beatmap.mode.value,
        beatmap_set_id=aiosu_beatmap.beatmapset_id,
        star_rating=aiosu_beatmap.difficulty_rating,
        ranked_status=aiosu_beatmap.status.value,
        total_length=aiosu_beatmap.total_length,
        creator_id=aiosu_beatmap.user_id,
        version=aiosu_beatmap.version,
        od=aiosu_beatmap.accuracy,
        ar=aiosu_beatmap.ar,
        cs=aiosu_beatmap.cs,
        hp=aiosu_beatmap.drain,
        bpm=aiosu_beatmap.bpm,
        convert=aiosu_beatmap.convert,
        num_circles=aiosu_beatmap.count_circles,
        num_sliders=aiosu_beatmap.count_sliders,
        num_spinners=aiosu_beatmap.count_spinners,
        deleted_at=aiosu_beatmap.deleted_at,
        hit_length=aiosu_beatmap.hit_length,
        is_scoreable=aiosu_beatmap.is_scoreable,
        last_updated=aiosu_beatmap.last_updated,
        passcount=aiosu_beatmap.passcount,
        play_count=aiosu_beatmap.play_count,
        beatmap_md5=aiosu_beatmap.checksum,
        max_combo=aiosu_beatmap.max_combo,
        beatmapset=BeatmapSet(
            beatmap_set_id=aiosu_beatmapset.id,
            artist=aiosu_beatmapset.artist,
            artist_unicode=aiosu_beatmapset.artist_unicode,
            covers=BeatmapCovers(
                cover=aiosu_beatmapset.covers.cover,
                card=aiosu_beatmapset.covers.card,
                list=aiosu_beatmapset.covers.list,
                slimcover=aiosu_beatmapset.covers.slimcover,
                cover_2_x=aiosu_beatmapset.covers.cover_2_x,
                card_2_x=aiosu_beatmapset.covers.card_2_x,
                list_2_x=aiosu_beatmapset.covers.list_2_x,
                slimcover_2_x=aiosu_beatmapset.covers.slimcover_2_x,
            ),
            creator_name=aiosu_beatmapset.creator,
            favourite_count=aiosu_beatmapset.favourite_count,
            play_count=aiosu_beatmapset.play_count,
            preview_url=aiosu_beatmapset.preview_url,
            source=aiosu_beatmapset.source,
            status=aiosu_beatmapset.status.value,
            title=aiosu_beatmapset.title,
            title_unicode=aiosu_beatmapset.title_unicode,
            creator_id=aiosu_beatmapset.user_id,
            video=aiosu_beatmapset.video,
            nsfw=aiosu_beatmapset.nsfw,
            hype=(
                BeatmapHype(
                    current=aiosu_beatmapset.hype.current,
                    required=aiosu_beatmapset.hype.required,
                )
                if aiosu_beatmapset.hype is not None
                else None
            ),
            availability=(
                BeatmapAvailability(
                    more_information=aiosu_beatmapset.availability.more_information,
                    download_disabled=aiosu_beatmapset.availability.download_disabled,
                )
                if aiosu_beatmapset.availability is not None
                else None
            ),
            bpm=aiosu_beatmapset.bpm,
            can_be_hyped=aiosu_beatmapset.can_be_hyped,
            discussion_enabled=aiosu_beatmapset.discussion_enabled,
            discussion_locked=aiosu_beatmapset.discussion_locked,
            is_scoreable=aiosu_beatmapset.is_scoreable,
            last_updated=aiosu_beatmapset.last_updated,
            legacy_thread_url=aiosu_beatmapset.legacy_thread_url,
            nominations_summary=BeatmapNominations(
                current=aiosu_beatmapset.nominations_summary.current,
                required=aiosu_beatmapset.nominations_summary.required,
            )
            if aiosu_beatmapset.nominations_summary is not None
            else None,
            ranked_date=aiosu_beatmapset.ranked_date,
            storyboard=aiosu_beatmapset.storyboard,
            submitted_date=aiosu_beatmapset.submitted_date,
            tags=aiosu_beatmapset.tags,
            ratings=aiosu_beatmapset.ratings,
            has_favourited=aiosu_beatmapset.has_favourited,
            beatmaps=(
                [beatmap_from_aiosu(beatmap) for beatmap in aiosu_beatmapset.beatmaps]
                if aiosu_beatmapset.beatmaps is not None
                else None
            ),
        ),
        failtimes=(
            BeatmapFailtimes(
                exit=aiosu_beatmap.failtimes.exit, fail=aiosu_beatmap.failtimes.fail
            )
            if aiosu_beatmap.failtimes is not None
            else None
        ),
    )


async def lookup_beatmap(
    beatmap_md5: str | None = None,
    file_name: str | None = None,
    beatmap_id: int | None = None,
) -> Beatmap | None:
    kwargs = {}
    if beatmap_md5 is not None:
        kwargs["checksum"] = beatmap_md5
    if file_name is not None:
        kwargs["filename"] = file_name
    if beatmap_id is not None:
        kwargs["beatmap_id"] = beatmap_id
    try:
        aiosu_beatmap = await clients.osu_api.lookup_beatmap(**kwargs)
    except aiosu.exceptions.APIException as exc:
        if exc.status == 404:
            aiosu_beatmap = None
        else:
            raise
    except Exception as exc:
        logger.error("Failed to fetch beatmap from osu! api", exc=exc)
        return

    if aiosu_beatmap is None:
        logger.warning(
            "Beatmap not found",
            checksum=beatmap_md5,
            filename=file_name,
            beatmap_id=beatmap_id,
        )
        return

    aiosu_beatmapset = aiosu_beatmap.beatmapset
    if aiosu_beatmapset is None:
        # TODO: handle this case
        logger.error(
            "Beatmapset is None",
            checksum=beatmap_md5,
            filename=file_name,
            beatmap_id=beatmap_id,
        )
        return

    assert aiosu_beatmap.checksum is not None
    assert aiosu_beatmap.last_updated is not None

    return beatmap_from_aiosu(aiosu_beatmap)


async def fetch_osu_file_contents(beatmap_id: int) -> bytes | None:
    # TODO: this is not technically part of api v2
    try:
        response = await clients.http_client.get(
            url=f"https://osu.ppy.sh/osu/{beatmap_id}",
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        else:
            raise
    except Exception as exc:
        logger.error("Failed to fetch beatmap from osu! api", exc=exc)
        return

    return await response.aread()
