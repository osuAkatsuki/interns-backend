class ClientPrivileges:
    """Client side user privileges."""

    PLAYER = 1 << 0
    MODERATOR = 1 << 1
    SUPPORTER = 1 << 2
    OWNER = 1 << 3
    DEVELOPER = 1 << 4
    TOURNAMENT = 1 << 5  # NOTE: not used in communications with osu! client


class ServerPrivileges:
    """Server side user privileges."""

    UNRESTRICTED = 1 << 0
    SUBMITTED_HARDWARE_IDENTITY = 1 << 1
    BEATMAP_NOMINATOR = 1 << 7
    CHAT_MODERATIOR = 1 << 9
    MULTIPLAYER_STAFF = 1 << 11
    ACCOUNT_MANAGEMENT = 1 << 13
    SUPER_ADMIN = 1 << 30


def server_to_client_privileges(value: int) -> int:
    # TODO: an actual function implementing this
    return (
        ClientPrivileges.PLAYER
        | ClientPrivileges.MODERATOR
        | ClientPrivileges.SUPPORTER
        | ClientPrivileges.OWNER
        | ClientPrivileges.DEVELOPER
        | ClientPrivileges.TOURNAMENT
    )
