#!/usr/bin/env python3
import base64
from datetime import datetime

from fastapi import APIRouter
from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi import UploadFile
from fastapi.responses import RedirectResponse
from py3rijndael import Pkcs7Padding
from py3rijndael import RijndaelCbc
from starlette.datastructures import UploadFile as _StarletteUploadFile

from server import achievement_handlers
from server import game_modes
from server import logger
from server import packets
from server import performance
from server import ranking
from server import security
from server.adapters import osu_api_v2
from server.adapters import s3
from server.errors import ServiceError
from server.privileges import ServerPrivileges
from server.repositories import accounts
from server.repositories import achievements
from server.repositories import packet_bundles
from server.repositories import relationships
from server.repositories import scores
from server.repositories import sessions
from server.repositories import stats
from server.repositories import user_achievements
from server.repositories.accounts import Account
from server.repositories.beatmaps import Beatmap
from server.repositories.scores import Score
from server.services import beatmaps
from server.services import screenshots

osu_web_router = APIRouter(default_response_class=Response)


@osu_web_router.get("/")
async def osu_web_home_page():
    return "Hello, osu!web!"


async def format_leaderboard_response(
    leaderboard_scores: list[Score],
    personal_best_score: Score | None,
    account: Account,
    beatmap: Beatmap,
) -> bytes:
    """\
    {ranked_status}|{serv_has_osz2}|{bid}|{bsid}|{len(scores)}|{fa_track_id}|{fa_license_text}
    {offset}\n{beatmap_name}\n{rating}
    {id}|{name}|{score}|{max_combo}|{n50}|{n100}|{n300}|{nmiss}|{nkatu}|{ngeki}|{perfect}|{mods}|{userid}|{rank}|{time}|{has_replay}
    {id}|{name}|{score}|{max_combo}|{n50}|{n100}|{n300}|{nmiss}|{nkatu}|{ngeki}|{perfect}|{mods}|{userid}|{rank}|{time}|{has_replay}
    ...
    """
    # 3rd line is peronsal best, rest are leaderboard scores

    buffer = ""

    # first line
    buffer += f"{2}|false|{beatmap['beatmap_id']}|{beatmap['beatmap_set_id']}|{len(leaderboard_scores)}|0|\n"

    # second line
    beatmap_name = "{artist} - {title} [{version}]".format(**beatmap)
    buffer += f"0\n{beatmap_name}\n{0.0}\n"  # TODO: beatmap rating

    # third line
    if personal_best_score is None:
        buffer += "\n"
    else:
        buffer += (
            f"{personal_best_score['score_id']}|"
            f"{account['username']}|"
            f"{personal_best_score['score']}|"
            f"{personal_best_score['highest_combo']}|"
            f"{personal_best_score['num_50s']}|"
            f"{personal_best_score['num_100s']}|"
            f"{personal_best_score['num_300s']}|"
            f"{personal_best_score['num_misses']}|"
            f"{personal_best_score['num_katus']}|"
            f"{personal_best_score['num_gekis']}|"
            f"{'1' if personal_best_score['full_combo'] else '0'}|"
            f"{personal_best_score['mods']}|"
            f"{account['account_id']}|"
            f"{1}|"  # TODO: leaderboard rank
            f"{int(personal_best_score['created_at'].timestamp())}|"
            f"{'1'}\n"  # TODO: has replay
        )

    # rest of the lines
    if not leaderboard_scores:
        buffer += "\n"
    else:
        for leaderboard_rank, score in enumerate(leaderboard_scores):
            # TODO: this is quite unfortuante that we need to lookup each user
            # an alternative might be to store the username in the score table
            # but the problem with that is that the username can change
            score_account = await accounts.fetch_by_account_id(score["account_id"])
            if score_account is None:
                logger.warning(
                    "Score has no account",
                    score_id=score["score_id"],
                    account_id=score["account_id"],
                )
                continue

            buffer += (
                f"{score['score_id']}|"
                f"{score_account['username']}|"
                f"{score['score']}|"
                f"{score['highest_combo']}|"
                f"{score['num_50s']}|"
                f"{score['num_100s']}|"
                f"{score['num_300s']}|"
                f"{score['num_misses']}|"
                f"{score['num_katus']}|"
                f"{score['num_gekis']}|"
                f"{'1' if score['full_combo'] else '0'}|"
                f"{score['mods']}|"
                f"{score['account_id']}|"
                f"{leaderboard_rank}|"
                f"{int(score['created_at'].timestamp())}|"
                f"{'1'}\n"  # TODO: has replay
            )

        # remove trailing "\n"
        buffer = buffer.removesuffix("\n")

    return buffer.encode()


# GET /web/osu-osz2-getscores.php
# ?s=0
# &vv=4
# &v=1
# &c=1cf5b2c2edfafd055536d2cefcb89c0e
# &f=FAIRY+FORE+-+Vivid+(Hitoshirenu+Shourai)+%5bInsane%5d.osu
# &m=0
# &i=141
# &mods=192
# &h=
# &a=0
# &us=cmyui
# &ha=0cc175b9c0f1b6a831c399e269772661
@osu_web_router.get("/web/osu-osz2-getscores.php")
async def get_scores_handler(
    username: str = Query(..., alias="us"),
    password_md5: str = Query(..., alias="ha"),
    requesting_score_data: bool = Query(..., alias="s"),
    leaderboard_version: int = Query(..., alias="vv"),
    leaderboard_type: int = Query(..., alias="v"),
    beatmap_md5: str = Query(..., alias="c"),
    beatmap_filename: str = Query(..., alias="f"),
    vanilla_game_mode: int = Query(..., alias="m"),
    beatmap_set_id: int = Query(..., alias="i"),
    mods: int = Query(..., alias="mods"),
    map_package_hash: str = Query(..., alias="h"),
    aqn_files_found: bool = Query(..., alias="a"),
):
    game_mode = game_modes.for_server(vanilla_game_mode, mods)

    # TODO: fix the responses in the case of an error
    account = await accounts.fetch_by_username(username)
    if account is None:
        return

    session = await sessions.fetch_by_username(username)
    if session is None:
        return

    # update user stats if they have changed
    # TODO: should we do this on more attributes?
    if game_mode != session["presence"]["game_mode"]:
        session = await sessions.partial_update(
            session["session_id"],
            game_mode=game_mode,
            mods=mods,
        )
        assert session is not None

        own_stats = await stats.fetch_one(session["account_id"], game_mode)
        assert own_stats is not None

        for other_session in await sessions.fetch_all():
            await packet_bundles.enqueue(
                other_session["session_id"],
                data=packets.write_user_stats_packet(
                    session["presence"]["account_id"],
                    session["presence"]["action"],
                    session["presence"]["info_text"],
                    session["presence"]["beatmap_md5"],
                    session["presence"]["mods"],
                    session["presence"]["game_mode"],
                    session["presence"]["beatmap_id"],
                    own_stats["ranked_score"],
                    own_stats["accuracy"],
                    own_stats["play_count"],
                    own_stats["total_score"],
                    ranking.get_global_rank(session["account_id"]),
                    own_stats["performance_points"],
                ),
            )

    if not security.check_password(
        password=password_md5,
        hashword=account["password"].encode(),
    ):
        return

    beatmap = await beatmaps.fetch_one(beatmap_md5=beatmap_md5)
    if isinstance(beatmap, ServiceError):
        if beatmap is ServiceError.BEATMAPS_NOT_FOUND:
            logger.warning("Beatmap not found", beatmap_md5=beatmap_md5)
            return

        logger.error(
            "Failed to fetch beatmap",
            beatmap_md5=beatmap_md5,
            error=beatmap,
        )
        return

    # TODO: leaderboard type handling

    leaderboard_scores = await scores.fetch_many(
        beatmap_md5=beatmap_md5,
        submission_status=2,  # TODO?
        game_mode=game_mode,
        sort_by="performance_points",  # TODO: score for certain gamemodes?
        page_size=50,
    )

    personal_best_scores = await scores.fetch_many(
        account_id=account["account_id"],
        beatmap_md5=beatmap_md5,
        submission_status=2,  # TODO?
        game_mode=game_mode,
        sort_by="performance_points",  # TODO: score for certain gamemodes?
        page_size=1,
    )
    if personal_best_scores:
        personal_best_score = personal_best_scores[0]
    else:
        personal_best_score = None

    response = await format_leaderboard_response(
        leaderboard_scores,
        personal_best_score,
        account,
        beatmap,
    )
    return response


def calculate_accuracy(
    num_300s: int,
    num_100s: int,
    num_50s: int,
    num_gekis: int,
    num_katus: int,
    num_misses: int,
) -> float:
    # TODO: support for all game modes

    total_notes = num_300s + num_100s + num_50s + num_misses

    accuracy = (
        ((num_300s * 3) + (num_100s * 1) + (num_50s * 0.5)) / total_notes * 100 / 3
    )
    return accuracy


@osu_web_router.post("/web/osu-submit-modular-selector.php")
async def submit_score_handler(
    request: Request,
    token: str = Header(...),
    exited_out: bool = Form(..., alias="x"),
    fail_time: int = Form(..., alias="ft"),
    visual_settings_b64: bytes = Form(..., alias="fs"),
    updated_beatmap_hash: str = Form(..., alias="bmk"),
    storyboard_md5: str | None = Form(None, alias="sbk"),
    iv_b64: bytes = Form(..., alias="iv"),
    unique_ids: str = Form(..., alias="c1"),
    score_time: int = Form(..., alias="st"),  # TODO: is this real name?
    password_md5: str = Form(..., alias="pass"),
    osu_version: str = Form(..., alias="osuver"),
    client_hash_aes_b64: bytes = Form(..., alias="s"),
    fl_cheat_screenshot: bytes | None = File(None, alias="i"),
):
    score_data_aes_b64, replay_file = (await request.form()).getlist("score")

    assert isinstance(score_data_aes_b64, str)
    assert isinstance(replay_file, _StarletteUploadFile)

    score_data_aes = base64.b64decode(score_data_aes_b64)
    client_hash_aes = base64.b64decode(client_hash_aes_b64)

    aes_cipher = RijndaelCbc(
        key=f"osu!-scoreburgr---------{osu_version}".encode(),
        iv=base64.b64decode(iv_b64),
        padding=Pkcs7Padding(block_size=32),
        block_size=32,
    )

    score_data = aes_cipher.decrypt(score_data_aes).decode().split(":")
    client_hash = aes_cipher.decrypt(client_hash_aes).decode()

    beatmap_md5 = score_data[0]
    username = score_data[1].removesuffix(" ")  # " " for supporter
    online_checksum = score_data[2]
    num_300s = int(score_data[3])
    num_100s = int(score_data[4])
    num_50s = int(score_data[5])
    num_gekis = int(score_data[6])
    num_katus = int(score_data[7])
    num_misses = int(score_data[8])
    score_points = int(score_data[9])
    highest_combo = int(score_data[10])
    full_combo = score_data[11] == "True"
    grade = score_data[12]

    mods = int(score_data[13])
    passed = score_data[14] == "True"
    vanilla_game_mode = int(score_data[15])
    client_time = datetime.strptime(score_data[16], "%y%m%d%H%M%S")
    client_anticheat_flags = score_data[17].count(" ") & ~4

    game_mode = game_modes.for_server(vanilla_game_mode, mods)

    account = await accounts.fetch_by_username(username)
    if account is None:
        logger.warning(f"Account {username} not found")
        return

    session = await sessions.fetch_by_username(username)
    if session is None:
        logger.warning(f"Session for {username} not found")
        return

    if not security.check_password(
        password=password_md5,
        hashword=account["password"].encode(),
    ):
        logger.warning(f"Invalid password for {username}")
        return

    beatmap = await beatmaps.fetch_one(beatmap_md5=beatmap_md5)
    if isinstance(beatmap, ServiceError):
        logger.warning("Beatmap not found", beatmap_md5=beatmap_md5)
        return

    # TODO: handle differently depending on beatmap ranked status

    # TODO: does this account for DT/HT?
    time_elapsed = score_time if passed else fail_time

    # TODO: set submission status based on performance vs. old scores
    # 2 = best score
    # 1 = passed
    # 0 = failed
    if passed:
        if "TODO: is best score":
            submission_status = 2
        else:
            submission_status = 1
    else:
        submission_status = 0

    accuracy = calculate_accuracy(
        num_300s,
        num_100s,
        num_50s,
        num_gekis,
        num_katus,
        num_misses,
    )

    try:
        osu_file_contents = await s3.download(
            filename=f"{beatmap['beatmap_id']}.osu",
            folder="osu_beatmap_files",
        )
        assert osu_file_contents is not None
    except Exception as exc:
        # TODO: JIT .osu files
        osu_file_contents = await osu_api_v2.fetch_osu_file_contents(
            beatmap["beatmap_id"]
        )
        if osu_file_contents is None:
            logger.error("Failed to download file from the osu! api")
            return

        try:
            await s3.upload(
                body=osu_file_contents,
                filename=f"{beatmap['beatmap_id']}.osu",
                folder="osu_beatmap_files",
            )
        except Exception as exc:
            logger.error("Failed to upload file to S3", exc_info=exc)
            return

    if osu_file_contents is None:
        logger.warning("Beatmap file for not found", beatmap_md5=beatmap_md5)
        return

    performance_attrs = performance.calculate_performance(
        osu_file_contents,
        vanilla_game_mode,
        mods,
        accuracy,
        num_300s,
        num_100s,
        num_50s,
        num_misses,
        num_gekis,
        num_katus,
        highest_combo,
    )

    score = await scores.create(
        account["account_id"],
        online_checksum,
        beatmap_md5,
        score_points,
        performance_attrs["performance_points"],
        accuracy,
        highest_combo,
        full_combo,
        mods,
        num_300s,
        num_100s,
        num_50s,
        num_misses,
        num_gekis,
        num_katus,
        grade,
        submission_status,
        game_mode,
        account["country"],  # TODO: should this be the session country?
        time_elapsed,
        client_anticheat_flags,
    )

    await s3.upload(
        body=await replay_file.read(),
        filename=f"{score['score_id']}.osr",
        folder="replays",
        acl="public-read",
    )

    # update beatmap stats (plays, passes)
    beatmap = await beatmaps.partial_update(
        beatmap["beatmap_id"],
        plays=beatmap["plays"] + 1,
        passes=beatmap["passes"] + 1 if passed else beatmap["passes"],
    )
    assert not isinstance(beatmap, ServiceError)

    # update account stats
    gamemode_stats = await stats.fetch_one(account["account_id"], game_mode)
    assert gamemode_stats is not None

    # TODO: these should be fetching pp-awarding scores only

    top_100_scores = await scores.fetch_many(
        account_id=account["account_id"],
        game_mode=game_mode,
        sort_by="performance_points",
        submission_status=2,
        page_size=100,
    )

    total_score_count = await scores.fetch_count(
        account_id=account["account_id"],
        submission_status=2,
        game_mode=game_mode,
    )

    # calculate new overall accuracy
    weighted_accuracy = sum(
        score["accuracy"] * 0.95**i for i, score in enumerate(top_100_scores)
    )
    if total_score_count:
        bonus_accuracy = 100.0 / (20 * (1 - 0.95**total_score_count))
    else:
        bonus_accuracy = 0.0

    total_accuracy = round((weighted_accuracy * bonus_accuracy) / 100.0, 3)

    # calculate new overall pp
    weighted_pp = sum(
        score["performance_points"] * 0.95**i
        for i, score in enumerate(top_100_scores)
    )
    bonus_pp = 416.6667 * (1 - 0.9994**total_score_count)
    total_pp = round(weighted_pp + bonus_pp)

    gamemode_stats = await stats.partial_update(
        account["account_id"],
        game_mode=game_mode,
        total_score=gamemode_stats["total_score"] + score_points,
        # TODO: only if best & on ranked map
        ranked_score=gamemode_stats["ranked_score"] + score_points,
        performance_points=total_pp,
        play_count=gamemode_stats["play_count"] + 1,
        play_time=gamemode_stats["play_time"] + time_elapsed,
        accuracy=total_accuracy,
        highest_combo=max(gamemode_stats["highest_combo"], highest_combo),
        total_hits=(
            gamemode_stats["total_hits"] + num_300s + num_100s + num_50s + num_misses
        ),
        xh_count=gamemode_stats["xh_count"] + (1 if grade == "XH" else 0),
        x_count=gamemode_stats["x_count"] + (1 if grade == "X" else 0),
        sh_count=gamemode_stats["sh_count"] + (1 if grade == "SH" else 0),
        s_count=gamemode_stats["s_count"] + (1 if grade == "S" else 0),
        a_count=gamemode_stats["a_count"] + (1 if grade == "A" else 0),
    )
    assert gamemode_stats is not None

    # send account stats to all other osu! sessions if we're not restricted
    if account["privileges"] & ServerPrivileges.UNRESTRICTED:
        sessions_to_notify = await sessions.fetch_all()
    else:
        sessions_to_notify = [session]

    for other_session in sessions_to_notify:
        packet_data = packets.write_user_stats_packet(
            gamemode_stats["account_id"],
            session["presence"]["action"],
            session["presence"]["info_text"],
            session["presence"]["beatmap_md5"],
            session["presence"]["mods"],
            vanilla_game_mode,
            session["presence"]["beatmap_id"],
            gamemode_stats["ranked_score"],
            gamemode_stats["accuracy"],
            gamemode_stats["play_count"],
            gamemode_stats["total_score"],
            ranking.get_global_rank(gamemode_stats["account_id"]),
            gamemode_stats["performance_points"],
        )
        await packet_bundles.enqueue(
            other_session["session_id"],
            packet_data,
        )

    # TODO: send to #announcements if the score is #1

    # unlock achievements
    current_achievement_ids = [
        a["achievement_id"]
        for a in await user_achievements.fetch_many(account_id=account["account_id"])
    ]
    new_achievements = []
    for achievement in await achievements.fetch_many():
        # user may have already unlocked this achievement
        if achievement["achievement_id"] in current_achievement_ids:
            continue

        handler = achievement_handlers.get_achievement_handler(
            achievement["achievement_id"]
        )

        # handler may not exist
        if handler is None:
            logger.warning(
                "Achievement handler not found",
                achievement_id=achievement["achievement_id"],
            )
            continue

        should_unlock = await handler(session, beatmap, score)

        # might not meet criteria
        if not should_unlock:
            continue

        new_achievement = await user_achievements.create(
            achievement["achievement_id"],
            account["account_id"],
        )

        new_achievements.append(new_achievement)

    # TODO: send achievements unlocked to client

    # TODO: construct score submission charts

    return b"error: no"


@osu_web_router.post("/difficulty-rating")
async def difficulty_rating_handler(request: Request):
    return RedirectResponse(
        url=f"https://osu.ppy.sh{request['path']}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@osu_web_router.get("/web/osu-getfriends.php")
async def friends_handler(
    username: str = Query(..., alias="u"),
    password: str = Query(..., alias="h"),
):
    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    if not security.check_password(
        password=password,
        hashword=account["password"].encode(),
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    friends = await relationships.fetch_all(
        account["account_id"],
        relationship="friend",
    )

    return "\n".join(str(friend["target_id"]) for friend in friends)


@osu_web_router.post("/web/osu-screenshot.php")
async def handle_screenshot_upload(
    endpoint_version: int = Form(..., alias="v"),
    screenshot_file: UploadFile = File(..., alias="ss"),
    username: str = Form(..., alias="u"),
    password: str = Form(..., alias="p"),
):
    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    if not security.check_password(
        password=password,
        hashword=account["password"].encode(),
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    file_data = await screenshot_file.read()

    screenshot = await screenshots.create(file_data)
    if isinstance(screenshot, ServiceError):
        logger.error("Screenshot upload failed!", error=screenshot)
        return

    return screenshot["download_url"]
