from enum import IntFlag


class ClientPrivileges(IntFlag):
    """Client side user privileges."""

    PLAYER = 1 << 0
    MODERATOR = 1 << 1
    SUPPORTER = 1 << 2
    OWNER = 1 << 3
    DEVELOPER = 1 << 4
    TOURNAMENT = 1 << 5  # NOTE: not used in communications with osu! client


class ServerPrivileges(IntFlag):
    """Server side user privileges."""

    ...


def server_to_client_privileges(value: int) -> ClientPrivileges:
    # TODO: an actual function implementing this
    return (
        ClientPrivileges.PLAYER
        | ClientPrivileges.MODERATOR
        | ClientPrivileges.SUPPORTER
        | ClientPrivileges.OWNER
        | ClientPrivileges.DEVELOPER
        | ClientPrivileges.TOURNAMENT
    )
