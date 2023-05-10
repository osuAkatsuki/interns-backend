from server import logger
from server.errors import ServiceError
from server.repositories import multiplayer_match_ids
from server.repositories import multiplayer_matches
from server.repositories.multiplayer_matches import MultiplayerMatch


async def create(
    match_name: str,
    match_password: str,
    beatmap_name: str,
    beatmap_id: int,
    beatmap_md5: str,
    host_account_id: int,
    game_mode: int,
    mods: int,
    win_condition: int,
    team_type: int,
    freemods_enabled: bool,
    random_seed: int,
) -> MultiplayerMatch | ServiceError:
    try:
        multiplayer_match_id = await multiplayer_match_ids.claim_id()

        match = await multiplayer_matches.create(
            multiplayer_match_id,
            match_name,
            match_password,
            beatmap_name,
            beatmap_id,
            beatmap_md5,
            host_account_id,
            game_mode,
            mods,
            win_condition,
            team_type,
            freemods_enabled,
            random_seed,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to create multiplayer match", exc_info=exc)
        return ServiceError.MULTIPLAYER_MATCHES_CREATE_FAILED

    return match


async def fetch_all() -> list[MultiplayerMatch] | ServiceError:
    try:
        matches = await multiplayer_matches.fetch_all()
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch multiplayer matches", exc_info=exc)
        return ServiceError.MULTIPLAYER_MATCHES_FETCH_ALL_FAILED

    return matches


async def fetch_one(match_id: int) -> MultiplayerMatch | ServiceError:
    try:
        match = await multiplayer_matches.fetch_one(match_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch multiplayer match", exc_info=exc)
        return ServiceError.MULTIPLAYER_MATCHES_FETCH_ONE_FAILED

    if match is None:
        return ServiceError.MULTIPLAYER_MATCHES_NOT_FOUND

    return match


async def partial_update(
    match_id: int,
    match_name: str | None,
    match_password: str | None,
    beatmap_name: str | None,
    beatmap_id: int | None,
    beatmap_md5: str | None,
    host_account_id: int | None,
    game_mode: int | None,  # enum
    mods: int | None,  # flags
    win_condition: int | None,  # enum
    team_type: int | None,  # enum
    freemods_enabled: bool | None,
    random_seed: int | None,
    status: int | None,  # enum
) -> MultiplayerMatch | ServiceError:
    try:
        match = await multiplayer_matches.partial_update(
            match_id,
            match_name,
            match_password,
            beatmap_name,
            beatmap_id,
            beatmap_md5,
            host_account_id,
            game_mode,
            mods,
            win_condition,
            team_type,
            freemods_enabled,
            random_seed,
            status,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to update multiplayer match", exc_info=exc)
        return ServiceError.MULTIPLAYER_MATCHES_UPDATE_FAILED

    if match is None:
        return ServiceError.MULTIPLAYER_MATCHES_NOT_FOUND

    return match


async def delete(match_id: int) -> MultiplayerMatch | ServiceError:
    try:
        match = await multiplayer_matches.delete(match_id)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to delete multiplayer match", exc_info=exc)
        return ServiceError.MULTIPLAYER_MATCHES_DELETE_FAILED

    if match is None:
        return ServiceError.MULTIPLAYER_MATCHES_NOT_FOUND

    return match
