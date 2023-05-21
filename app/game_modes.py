class GameMode:
    VN_OSU = 0
    VN_TAIKO = 1
    VN_CATCH = 2
    VN_MANIA = 3
    RX_OSU = 4
    RX_TAIKO = 5
    RX_CATCH = 6
    # RX_MANIA = 7  # doesn't exist
    AP_OSU = 8
    # AP_TAIKO = 9  # doesn't exist
    # AP_CATCH = 10  # doesn't exist
    # AP_MANIA = 11  # doesn't exist


def for_client(server_game_mode: int) -> int:
    game_mode = server_game_mode
    if game_mode == GameMode.AP_OSU:
        return GameMode.VN_OSU
    elif game_mode >= GameMode.RX_OSU:
        return (game_mode - GameMode.RX_OSU)
    else:
        return game_mode


def for_server(client_game_mode: int, mods: int) -> int:
    game_mode = client_game_mode
    if mods & 128:  # relax
        game_mode += 4
    if mods & 8192:  # autopilot
        game_mode += 8
    return game_mode
