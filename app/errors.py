from enum import Enum


class ServiceError(str, Enum):
    INTERNAL_SERVER_ERROR = "global.internal_server_error"

    ACCOUNTS_NOT_FOUND = "accounts.not_found"
    ACCOUNTS_USERNAME_INVALID = "accounts.username_invalid"
    ACCOUNTS_PASSWORD_INVALID = "accounts.password_invalid"
    ACCOUNTS_EMAIL_ADDRESS_INVALID = "accounts.email_address_invalid"
    ACCOUNTS_EMAIL_ADDRESS_EXISTS = "accounts.email_address_exists"
    ACCOUNTS_USERNAME_EXISTS = "accounts.username_exists"
    ACCOUNTS_COUNTRY_INVALID = "accounts.country_invalid"

    OSU_SESSIONS_NOT_FOUND = "osu_sessions.not_found"
    OSU_SESSIONS_CREATE_FAILED = "osu_sessions.create_failed"
    OSU_SESSIONS_FETCH_BY_ID_FAILED = "osu_sessions.fetch_by_id_failed"
    OSU_SESSIONS_FETCH_MANY_FAILED = "osu_sessions.fetch_many_failed"
    OSU_SESSIONS_FETCH_TOTAL_COUNT_FAILED = "osu_sessions.fetch_total_count_failed"
    OSU_SESSIONS_FETCH_ALL_FAILED = "osu_sessions.fetch_all_failed"
    OSU_SESSIONS_UPDATE_FAILED = "osu_sessions.update_failed"
    OSU_SESSIONS_DELETE_FAILED = "osu_sessions.delete_failed"

    CREDENTIALS_NOT_FOUND = "credentials.incorrect_credentials"
    CREDENTIALS_INCORRECT = "credentials.incorrect_credentials"

    SCREENSHOTS_IMAGE_INVALID = "screenshots.image_invalid"
    SCREENSHOTS_NOT_FOUND = "screenshots.not_found"

    MULTIPLAYER_MATCHES_CREATE_FAILED = "multiplayer_matches.create_failed"
    MULTIPLAYER_MATCHES_FETCH_ALL_FAILED = "multiplayer_matches.fetch_all_failed"
    MULTIPLAYER_MATCHES_FETCH_ONE_FAILED = "multiplayer_matches.fetch_one_failed"
    MULTIPLAYER_MATCHES_UPDATE_FAILED = "multiplayer_matches.update_failed"
    MULTIPLAYER_MATCHES_DELETE_FAILED = "multiplayer_matches.delete_failed"
    MULTIPLAYER_MATCHES_NOT_FOUND = "multiplayer_matches.not_found"

    BEATMAPS_CREATE_FAILED = "beatmaps.create_failed"
    BEATMAPS_NOT_FOUND = "beatmaps.not_found"

    SCORES_NOT_FOUND = "scores.not_found"
