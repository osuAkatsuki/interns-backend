#!/usr/bin/env python3
import base64
import copy
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

from app import achievement_handlers
from app import game_modes
from app import logger
from app import packets
from app import performance
from app import ranked_statuses
from app import ranking
from app import security
from app.adapters import mino
from app.adapters import osu_api_v2
from app.adapters import s3
from app.errors import ServiceError
from app.game_modes import GameMode
from app.mods import filter_invalid_mod_combinations
from app.privileges import ServerPrivileges
from app.ranked_statuses import BeatmapRankedStatus
from app.ranked_statuses import BeatmapWebRankedStatus
from app.repositories import accounts
from app.repositories import achievements
from app.repositories import channel_members
from app.repositories import channels
from app.repositories import osu_sessions
from app.repositories import packet_bundles
from app.repositories import relationships
from app.repositories import scores
from app.repositories import stats
from app.repositories import user_achievements
from app.repositories.accounts import Account
from app.repositories.beatmaps import Beatmap
from app.repositories.scores import Score
from app.repositories.scores import SubmissionStatus
from app.services import beatmaps
from app.services import screenshots

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
    web_ranked_status = ranked_statuses.to_web_status(beatmap["ranked_status"])
    buffer += f"{web_ranked_status}|false|{beatmap['beatmap_id']}|{beatmap['beatmap_set_id']}|{len(leaderboard_scores)}|0|\n"

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


class LeaderboardType:
    Local = 0
    Global = 1
    Mods = 2
    Friends = 3
    Country = 4


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
    # XXX: this is a quirk of the osu! client, where it adjusts this value
    # only after it sends the packet to the server; so we need to adjust
    mods = filter_invalid_mod_combinations(mods, vanilla_game_mode)

    game_mode = game_modes.for_server(vanilla_game_mode, mods)

    # TODO: fix the responses in the case of an error
    account = await accounts.fetch_by_username(username)
    if account is None:
        return

    # check that password is correct
    if not security.check_password(
        password=password_md5,
        hashword=account["password"].encode(),
    ):
        return

    osu_session = await osu_sessions.fetch_primary_by_username(username)
    if osu_session is None:
        return

    # update user stats if they have changed
    # TODO: should we do this on more attributes?
    if game_mode != osu_session["game_mode"]:
        osu_session = await osu_sessions.partial_update(
            osu_session["osu_session_id"],
            game_mode=game_mode,
            mods=mods,
        )
        assert osu_session is not None

        own_stats = await stats.fetch_one(osu_session["account_id"], game_mode)
        assert own_stats is not None

        own_global_rank = await ranking.get_global_rank(
            own_stats["account_id"],
            own_stats["game_mode"],
        )

        for other_osu_session in await osu_sessions.fetch_all():
            await packet_bundles.enqueue(
                other_osu_session["osu_session_id"],
                data=packets.write_user_stats_packet(
                    osu_session["account_id"],
                    osu_session["action"],
                    osu_session["info_text"],
                    osu_session["beatmap_md5"],
                    osu_session["mods"],
                    osu_session["game_mode"],
                    osu_session["beatmap_id"],
                    own_stats["ranked_score"],
                    own_stats["accuracy"],
                    own_stats["play_count"],
                    own_stats["total_score"],
                    own_global_rank,
                    own_stats["performance_points"],
                ),
            )

    # fetch the beatmap with this md5
    beatmap = await beatmaps.fetch_one(beatmap_md5=beatmap_md5)
    if isinstance(beatmap, ServiceError):
        if beatmap is ServiceError.BEATMAPS_NOT_FOUND:
            beatmap = await beatmaps.fetch_one(file_name=beatmap_filename)
            if beatmap is not ServiceError.BEATMAPS_NOT_FOUND:
                return f"{BeatmapWebRankedStatus.UPDATE_AVAILABLE}|false".encode()

            logger.debug("Beatmap not found", beatmap_md5=beatmap_md5)
            return f"{BeatmapWebRankedStatus.NOT_SUBMITTED}|false".encode()

        logger.error(
            "Failed to fetch beatmap",
            beatmap_md5=beatmap_md5,
            error=beatmap,
        )
        return f"{BeatmapWebRankedStatus.NOT_SUBMITTED}|false".encode()

    # create filter parameters for score fetching
    # based on the leaderboard type
    filter_params = {
        "beatmap_md5": beatmap_md5,
        "game_mode": game_mode,
        "submission_statuses": [SubmissionStatus.BEST],
        "sort_by": "performance_points",  # TODO: score for certain gamemodes?
    }

    fetch_scores = scores.fetch_many

    if leaderboard_type == LeaderboardType.Mods:
        fetch_scores = scores.fetch_best_for_each_account
        filter_params["mods"] = mods

    elif leaderboard_type == LeaderboardType.Country:
        filter_params["country"] = account["country"]

    elif leaderboard_type == LeaderboardType.Friends:
        friends = await relationships.fetch_all(
            account_id=account["account_id"],
            relationship="friend",
        )
        filter_params["friends"] = [osu_session["account_id"]] + [
            friend["account_id"] for friend in friends
        ]

    # fetch our top 50 scores for the leaderboard
    leaderboard_scores = await fetch_scores(**filter_params, page_size=50)

    # fetch our personal best score for the beatmap
    filter_params |= {
        "account_id": account["account_id"],  # we want our best
        "country": None,  # we want our global best
    }
    personal_best_scores = await fetch_scores(**filter_params, page_size=1)
    personal_best_score = personal_best_scores[0] if personal_best_scores else None

    # construct and send the leaderboard response
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
    vanilla_game_mode: int,
) -> float:
    if vanilla_game_mode == GameMode.VN_OSU:
        total_notes = num_300s + num_100s + num_50s + num_misses

        accuracy = (
            100.0
            * ((num_300s * 300.0) + (num_100s * 100.0) + (num_50s * 50.0))
            / (total_notes * 300.0)
        )
    elif vanilla_game_mode == GameMode.VN_TAIKO:
        total_notes = num_300s + num_100s + num_misses

        accuracy = 100.0 * ((num_100s * 0.5) + num_300s) / total_notes
    elif vanilla_game_mode == GameMode.VN_CATCH:
        total_notes = num_300s + num_100s + num_50s + num_katus + num_misses

        accuracy = 100.0 * (num_300s + num_100s + num_50s) / total_notes
    elif vanilla_game_mode == GameMode.VN_MANIA:
        total_notes = num_300s + num_100s + num_50s + num_gekis + num_katus + num_misses

        accuracy = (
            100.0
            * (
                (num_50s * 50.0)
                + (num_100s * 100.0)
                + (num_katus * 200.0)
                + ((num_300s + num_gekis) * 300.0)
            )
            / (total_notes * 300.0)
        )
    else:
        raise ValueError(f"Invalid vanilla mode: {vanilla_game_mode}")

    return accuracy


class ScoreSubmissionErrors:
    HANDLE_PASSWORD_RESET = "reset"
    REQUIRE_VERIFICATION = "verify"
    NO_SUCH_USER = "nouser"
    NEEDS_AUTHENTICATION = "pass"
    ACCOUNT_INACTIVE = "inactive"
    ACCOUNT_BANNED = "ban"
    BEATMAP_UNRANKED = "beatmap"
    MODE_OR_MODS_DISABLED = "disabled"
    OLD_OSU_VERSION = "oldver"
    NO = "no"


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
    # this may be null in the case where the osu! updater ran before client startup.
    # TODO: how can we ensure this? surely bancho doesn't just let it slide
    client_anticheat_token: str | None = Header(None, alias="Token"),
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
        return f"error: {ScoreSubmissionErrors.NEEDS_AUTHENTICATION}"

    osu_session = await osu_sessions.fetch_primary_by_username(username)
    if osu_session is None:
        logger.warning(f"osu! session for {username} not found")
        return f"error: {ScoreSubmissionErrors.NEEDS_AUTHENTICATION}"

    if not security.check_password(
        password=password_md5,
        hashword=account["password"].encode(),
    ):
        logger.warning(f"Invalid password for {username}")
        return f"error: {ScoreSubmissionErrors.NEEDS_AUTHENTICATION}"

    beatmap = await beatmaps.fetch_one(beatmap_md5=beatmap_md5)
    if isinstance(beatmap, ServiceError):
        logger.debug("Beatmap not found", beatmap_md5=beatmap_md5)
        return f"error: {ScoreSubmissionErrors.BEATMAP_UNRANKED}"

    # TODO: handle differently depending on beatmap ranked status

    # TODO: does this account for DT/HT?
    time_elapsed = score_time if passed else fail_time

    accuracy = calculate_accuracy(
        num_300s,
        num_100s,
        num_50s,
        num_gekis,
        num_katus,
        num_misses,
        vanilla_game_mode,
    )

    try:
        osu_file_contents = await s3.download(
            filename=f"{beatmap['beatmap_id']}.osu",
            folder="osu_beatmap_files",
        )
        assert osu_file_contents is not None
    except Exception as exc:
        osu_file_contents = await osu_api_v2.fetch_osu_file_contents(
            beatmap["beatmap_id"]
        )
        if osu_file_contents is None:
            logger.error("Failed to download file from the osu! api")
            return f"error: {ScoreSubmissionErrors.BEATMAP_UNRANKED}"

        try:
            await s3.upload(
                body=osu_file_contents,
                filename=f"{beatmap['beatmap_id']}.osu",
                folder="osu_beatmap_files",
            )
        except Exception as exc:
            logger.error("Failed to upload file to S3", exc_info=exc)
            return f"error: {ScoreSubmissionErrors.BEATMAP_UNRANKED}"

    if osu_file_contents is None:
        logger.warning("Beatmap file for not found", beatmap_md5=beatmap_md5)
        return f"error: {ScoreSubmissionErrors.BEATMAP_UNRANKED}"

    # calculate beatmap difficulty and score performance
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

    # determine score submission status
    if passed:
        previous_bests = await scores.fetch_many(
            beatmap_md5=beatmap["beatmap_md5"],
            account_id=account["account_id"],
            submission_statuses=[SubmissionStatus.BEST],
            page_size=1,
        )
        previous_best_score = previous_bests[0] if previous_bests else None

        is_new_best = (
            performance_attrs["performance_points"]
            > previous_best_score["performance_points"]
            if previous_best_score is not None
            else True
        )

        if is_new_best:
            submission_status = SubmissionStatus.BEST
            if previous_best_score is not None:
                await scores.partial_update(
                    score_id=previous_best_score["score_id"],
                    submission_status=SubmissionStatus.SUBMITTED,
                )
        else:
            submission_status = SubmissionStatus.SUBMITTED
    else:
        previous_best_score = None
        submission_status = SubmissionStatus.FAILED

    # persist new score to database
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
        client_anticheat_token,
    )

    # upload replay file to S3
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

    top_100_scores = await scores.fetch_many(
        account_id=account["account_id"],
        game_mode=game_mode,
        sort_by="performance_points",
        submission_statuses=[SubmissionStatus.BEST],
        beatmap_ranked_statuses=[
            BeatmapRankedStatus.RANKED,
            BeatmapRankedStatus.APPROVED,
        ],
        page_size=100,
    )

    total_score_count = await scores.fetch_total_count(
        account_id=account["account_id"],
        submission_statuses=[SubmissionStatus.BEST],
        beatmap_ranked_statuses=[
            BeatmapRankedStatus.RANKED,
            BeatmapRankedStatus.APPROVED,
        ],
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

    # create a copy of the previous gamemode's stats.
    # we will use this to construct overall ranking charts for the client
    previous_gamemode_stats = copy.deepcopy(gamemode_stats)
    previous_global_rank = await ranking.get_global_rank(
        gamemode_stats["account_id"],
        gamemode_stats["game_mode"],
    )

    new_ranked_score = gamemode_stats["ranked_score"]
    if score["submission_status"] == SubmissionStatus.BEST and score[
        "beatmap_ranked_status"
    ] in (BeatmapRankedStatus.RANKED, BeatmapRankedStatus.APPROVED):
        new_ranked_score += score_points

        if previous_best_score is not None:
            new_ranked_score -= previous_best_score["score"]

    # update this gamemode's stats with our new score submission
    gamemode_stats = await stats.partial_update(
        account["account_id"],
        game_mode=game_mode,
        total_score=gamemode_stats["total_score"] + score_points,
        ranked_score=new_ranked_score,
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
        osu_sessions_to_notify = await osu_sessions.fetch_all()
    else:
        osu_sessions_to_notify = [osu_session]

    own_global_rank = await ranking.get_global_rank(
        gamemode_stats["account_id"],
        gamemode_stats["game_mode"],
    )

    for other_osu_session in osu_sessions_to_notify:
        packet_data = packets.write_user_stats_packet(
            gamemode_stats["account_id"],
            osu_session["action"],
            osu_session["info_text"],
            osu_session["beatmap_md5"],
            osu_session["mods"],
            vanilla_game_mode,
            osu_session["beatmap_id"],
            gamemode_stats["ranked_score"],
            gamemode_stats["accuracy"],
            gamemode_stats["play_count"],
            gamemode_stats["total_score"],
            own_global_rank,
            gamemode_stats["performance_points"],
        )
        await packet_bundles.enqueue(
            other_osu_session["osu_session_id"],
            packet_data,
        )

    score_rank = 1  # TODO

    # if this score is #1, send it to the #announce channel
    if score["submission_status"] == SubmissionStatus.BEST and score_rank == 1:
        announce_channel = await channels.fetch_one_by_name("#announce")
        if announce_channel is not None:
            beatmap_embed = beatmaps.create_beatmap_chat_embed(
                beatmap["beatmap_set_id"],
                beatmap["beatmap_id"],
                beatmap["artist"],
                beatmap["title"],
                beatmap["version"],
                beatmap["creator"],
                mode_string="osu",
            )

            packet_data = packets.write_send_message_packet(
                sender_name="BanchoBot",
                message_content=f"{username} achieved a new #1 score on {beatmap_embed}!",
                recipient_name="#announce",
                sender_id=0,
            )

            announce_channel_members = await channel_members.members(
                announce_channel["channel_id"]
            )
            for osu_session_id in announce_channel_members:
                await packet_bundles.enqueue(osu_session_id, packet_data)

    # unlock achievements
    own_achievements = await user_achievements.fetch_many(
        account_id=account["account_id"]
    )
    own_achievement_ids = [ach["achievement_id"] for ach in own_achievements]

    new_achievements: list[achievements.Achievement] = []
    for achievement in await achievements.fetch_many():
        # user may have already unlocked this achievement
        if achievement["achievement_id"] in own_achievement_ids:
            continue

        achievement_handler = achievement_handlers.get_achievement_handler(
            achievement["achievement_id"]
        )

        # handler may not exist
        if achievement_handler is None:
            logger.warning(
                "Achievement handler not found",
                achievement_id=achievement["achievement_id"],
            )
            continue

        unlocked = await achievement_handler(osu_session, beatmap, score)

        # might not meet criteria
        if not unlocked:
            continue

        await user_achievements.create(
            achievement["achievement_id"],
            account["account_id"],
        )

        new_achievements.append(achievement)

    # build beatmap ranking chart values
    if previous_best_score:
        beatmap_rank_before = 0  # TODO
        beatmap_ranked_score_before = previous_best_score["score"]
        beatmap_total_score_before = previous_best_score["score"]
        beatmap_max_combo_before = previous_best_score["highest_combo"]
        beatmap_accuracy_before = previous_best_score["accuracy"]
        beatmap_pp_before = previous_best_score["performance_points"]
    else:
        beatmap_rank_before = ""
        beatmap_ranked_score_before = ""
        beatmap_total_score_before = ""
        beatmap_max_combo_before = ""
        beatmap_accuracy_before = ""
        beatmap_pp_before = ""
    beatmap_rank_after = 0  # TODO
    beatmap_ranked_score_after = score["score"]
    beatmap_total_score_after = score["score"]
    beatmap_max_combo_after = score["highest_combo"]
    beatmap_accuracy_after = score["accuracy"]
    beatmap_pp_after = score["performance_points"]

    # build overall ranking chart values
    overall_rank_before = previous_global_rank
    overall_rank_after = own_global_rank
    overall_ranked_score_before = previous_gamemode_stats["ranked_score"]
    overall_ranked_score_after = gamemode_stats["ranked_score"]
    overall_total_score_before = previous_gamemode_stats["total_score"]
    overall_total_score_after = gamemode_stats["total_score"]
    overall_max_combo_before = previous_gamemode_stats["highest_combo"]
    overall_max_combo_after = gamemode_stats["highest_combo"]
    overall_accuracy_before = previous_gamemode_stats["accuracy"]
    overall_accuracy_after = gamemode_stats["accuracy"]
    overall_pp_before = previous_gamemode_stats["performance_points"]
    overall_pp_after = gamemode_stats["performance_points"]

    # construct response data
    response_data = bytearray()

    # add overall and beatmap ranking charts to response data
    response_data += (
        f"beatmapId:{beatmap['beatmap_id']}|"
        f"beatmapSetId:{beatmap['beatmap_set_id']}|"
        f"beatmapPlaycount:{beatmap['plays']}|"
        f"beatmapPasscount:{beatmap['passes']}|"
        f"approvedDate:{beatmap['created_at'].isoformat()}|"
        "\n"
        "|chartId:beatmap|"
        f"chartUrl:https://osu.ppy.sh/beatmapsets/{beatmap['beatmap_set_id']}|"
        "chartName:Beatmap Ranking|"
        f"rankBefore:{beatmap_rank_before}|"
        f"rankAfter:{beatmap_rank_after}|"
        f"rankedScoreBefore:{beatmap_ranked_score_before}|"
        f"rankedScoreAfter:{beatmap_ranked_score_after}|"
        f"totalScoreBefore:{beatmap_total_score_before}|"
        f"totalScoreAfter:{beatmap_total_score_after}|"
        f"maxComboBefore:{beatmap_max_combo_before}|"
        f"maxComboAfter:{beatmap_max_combo_after}|"
        f"accuracyBefore:{beatmap_accuracy_before}|"
        f"accuracyAfter:{beatmap_accuracy_after}|"
        f"ppBefore:{beatmap_pp_before}|"
        f"ppAfter:{beatmap_pp_after}|"
        f"onlineScoreId:{score['score_id']}|"
        "\n"
        "|chartId:overall|"
        f"chartUrl:https://osu.ppy.sh/u/{account['account_id']}|"
        "chartName:Overall Ranking|"
        f"rankBefore:{overall_rank_before}|"
        f"rankAfter:{overall_rank_after}|"
        f"rankedScoreBefore:{overall_ranked_score_before}|"
        f"rankedScoreAfter:{overall_ranked_score_after}|"
        f"totalScoreBefore:{overall_total_score_before}|"
        f"totalScoreAfter:{overall_total_score_after}|"
        f"maxComboBefore:{overall_max_combo_before}|"
        f"maxComboAfter:{overall_max_combo_after}|"
        f"accuracyBefore:{overall_accuracy_before}|"
        f"accuracyAfter:{overall_accuracy_after}|"
        f"ppBefore:{overall_pp_before}|"
        f"ppAfter:{overall_pp_after}|"
    ).encode()

    # add newly unlocked achievements to response data
    achievements_string = "/".join(
        [achievements.to_string(ach) for ach in new_achievements]
    )
    response_data += f"achievements-new:{achievements_string}".encode()

    return bytes(response_data)


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
async def screenshot_upload_handler(
    endpoint_version: int = Form(..., alias="v"),
    screenshot_file: UploadFile = File(..., alias="ss"),
    username: str = Form(..., alias="u"),
    password: str = Form(..., alias="p"),
):
    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

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


@osu_web_router.get("/web/osu-search.php")
async def osu_search_handler(
    username: str = Query(..., alias="u"),
    password: str = Query(..., alias="h"),
    ranked_status: int = Query(..., alias="r"),
    query: str = Query(..., alias="q"),
    game_mode: int = Query(..., alias="m"),  # -1 for all
    page: int = Query(..., alias="p"),
):
    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if not security.check_password(
        password=password,
        hashword=account["password"].encode(),
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    response_data = await mino.osudirect_search(
        query,
        game_mode,
        ranked_status,
        page,
    )
    return response_data


@osu_web_router.get("/web/osu-search-set.php")
async def osu_search_set_handler(
    username: str = Query(..., alias="u"),
    password: str = Query(..., alias="h"),
    beatmap_set_id: int | None = Query(None, alias="s"),
    beatmap_id: int | None = Query(None, alias="b"),
):
    if beatmap_set_id is None and beatmap_id is None:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if not security.check_password(
        password=password,
        hashword=account["password"].encode(),
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if beatmap_set_id is not None:
        response_data = await mino.get_beatmap_set(beatmap_set_id)
    elif beatmap_id is not None:
        response_data = await mino.get_beatmap(beatmap_id)
    else:  # pragma: no cover
        raise NotImplementedError  # unreachable

    # the response format resembles;
    "{set_id}.osz|{artist}|{title}|{creator}|{status}|{beatmap_rating}|{last_update}|"
    "{set_id}|{thread_id}|{has_video}|{has_storyboard}|{filesize}|{filesize_novideo}"

    return response_data


@osu_web_router.get("/d/{beatmap_set_id}")
async def download_beatmap_set_handler(
    beatmap_set_id: int,
    username: str = Query(..., alias="u"),
    password: str = Query(..., alias="h"),
    endpoint_version: int = Query(..., alias="vv"),
):
    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if not security.check_password(
        password=password,
        hashword=account["password"].encode(),
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    return RedirectResponse(
        url=f"https://catboy.best/d/{beatmap_set_id}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


@osu_web_router.get("/web/osu-getreplay.php")
async def get_replay_handler(
    username: str = Query(..., alias="u"),
    password: str = Query(..., alias="h"),
    score_id: int = Query(..., alias="c"),
):
    account = await accounts.fetch_by_username(username)

    if account is None:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    if not security.check_password(
        password=password,
        hashword=account["password"].encode(),
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    score = await scores.fetch_one_by_id(score_id=score_id)
    if score is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    replay_data = await s3.download(
        filename=f"{score['score_id']}.osr",
        folder="replays",
    )
    if replay_data is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return Response(replay_data, media_type="application/octet-stream")


@osu_web_router.get("/web/maps/{beatmap_filename}")
async def get_updated_beatmap_handler(beatmap_filename: str):
    return RedirectResponse(
        url=f"https://osu.ppy.sh/web/maps/{beatmap_filename}",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
