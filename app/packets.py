import struct
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import NotRequired
from typing import TypedDict

# packets are comprised of 3 parts:
# - a unique identifier (the packet id), representing the type of request
# - the length of the request data
# - request data; specific to the packet id

# the packet id is sent over the wire as an unsigned short (2 bytes, u16)
# the packet data length is sent as an unsigned long (4 bytes, u32)
# the packet data
# - is of variable length
# - may comprise of multiple objects
# - is specific to the request type (packet id)
# - types can vary, but are from a fixed set of possibilities (u8, u16, u32, u64, i8, i16, i32, i64, f32, f64, string, and some higher level types comprising of these primitives)

# osu! packets are sent in "little endian" ordering.
# little endian: [2, 0, 0, 0] == 2
# big endian: [0, 0, 0, 2] == 2


class ClientPackets:
    CHANGE_ACTION = 0
    SEND_PUBLIC_MESSAGE = 1
    OSU_EXIT = 2
    REQUEST_STATUS_UPDATE = 3
    PING = 4
    START_SPECTATING = 16
    STOP_SPECTATING = 17
    SPECTATE_FRAMES = 18
    ERROR_REPORT = 20  # unused
    CANT_SPECTATE = 21
    SEND_PRIVATE_MESSAGE = 25
    PART_LOBBY = 29
    JOIN_LOBBY = 30
    CREATE_MATCH = 31
    JOIN_MATCH = 32
    PART_MATCH = 33
    MATCH_CHANGE_SLOT = 38
    MATCH_READY = 39
    MATCH_LOCK = 40
    MATCH_CHANGE_SETTINGS = 41
    MATCH_START = 44
    MATCH_SCORE_UPDATE = 47
    MATCH_COMPLETE = 49
    MATCH_CHANGE_MODS = 51
    MATCH_LOAD_COMPLETE = 52
    MATCH_NO_BEATMAP = 54
    MATCH_NOT_READY = 55
    MATCH_FAILED = 56
    MATCH_HAS_BEATMAP = 59
    MATCH_SKIP_REQUEST = 60
    CHANNEL_JOIN = 63
    BEATMAP_INFO_REQUEST = 68  # unused
    MATCH_TRANSFER_HOST = 70
    FRIEND_ADD = 73
    FRIEND_REMOVE = 74
    MATCH_CHANGE_TEAM = 77
    CHANNEL_PART = 78
    RECEIVE_UPDATES = 79
    SET_AWAY_MESSAGE = 82
    IRC_ONLY = 84
    USER_STATS_REQUEST = 85
    MATCH_INVITE = 87
    MATCH_CHANGE_PASSWORD = 90
    TOURNAMENT_MATCH_INFO_REQUEST = 93
    USER_PRESENCE_REQUEST = 97
    USER_PRESENCE_REQUEST_ALL = 98
    TOGGLE_BLOCK_NON_FRIEND_DMS = 99
    TOURNAMENT_JOIN_MATCH_CHANNEL = 108
    TOURNAMENT_LEAVE_MATCH_CHANNEL = 109


class ServerPackets:
    USER_ID = 5
    SEND_MESSAGE = 7
    PONG = 8
    HANDLE_IRC_CHANGE_USERNAME = 9  # unused
    HANDLE_IRC_QUIT = 10
    USER_STATS = 11
    USER_LOGOUT = 12
    SPECTATOR_JOINED = 13
    SPECTATOR_LEFT = 14
    SPECTATE_FRAMES = 15
    VERSION_UPDATE = 19
    SPECTATOR_CANT_SPECTATE = 22
    GET_ATTENTION = 23
    NOTIFICATION = 24
    UPDATE_MATCH = 26
    NEW_MATCH = 27
    DISPOSE_MATCH = 28
    LOBBY_JOIN_UNUSED = 34  # unused
    MATCH_JOIN_SUCCESS = 36
    MATCH_JOIN_FAIL = 37
    FELLOW_SPECTATOR_JOINED = 42
    FELLOW_SPECTATOR_LEFT = 43
    ALL_PLAYERS_LOADED = 45  # unused
    MATCH_START = 46
    MATCH_SCORE_UPDATE = 48
    MATCH_TRANSFER_HOST = 50
    MATCH_ALL_PLAYERS_LOADED = 53
    MATCH_PLAYER_FAILED = 57
    MATCH_COMPLETE = 58
    MATCH_SKIP = 61
    UNAUTHORIZED = 62  # unused
    CHANNEL_JOIN_SUCCESS = 64
    CHANNEL_INFO = 65
    CHANNEL_KICK = 66
    CHANNEL_AUTO_JOIN = 67
    BEATMAP_INFO_REPLY = 69
    PRIVILEGES = 71
    FRIENDS_LIST = 72
    PROTOCOL_VERSION = 75
    MAIN_MENU_ICON = 76
    MONITOR = 80  # unused
    MATCH_PLAYER_SKIPPED = 81
    USER_PRESENCE = 83
    RESTART = 86
    MATCH_INVITE = 88
    CHANNEL_INFO_END = 89
    MATCH_CHANGE_PASSWORD = 91
    SILENCE_END = 92
    USER_SILENCED = 94
    USER_PRESENCE_SINGLE = 95
    USER_PRESENCE_BUNDLE = 96
    USER_DM_BLOCKED = 100
    TARGET_IS_SILENCED = 101
    VERSION_UPDATE_FORCED = 102
    SWITCH_SERVER = 103
    ACCOUNT_RESTRICTED = 104
    RTX = 105  # unused
    MATCH_ABORT = 106
    SWITCH_TOURNAMENT_SERVER = 107


@dataclass
class Packet:
    packet_id: int
    packet_data_length: int
    packet_data: bytes


class OsuMessage(TypedDict):
    sender_name: str
    message_content: str
    recipient_name: str
    sender_id: int


class OsuChannel(TypedDict):
    channel_name: str
    channel_topic: str
    channel_user_count: int


class OsuMatch(TypedDict):
    match_id: int
    match_in_progress: bool
    mods: int
    match_name: str
    match_password: str
    beatmap_name: str
    beatmap_id: int
    beatmap_md5: str
    slot_statuses: list[int]
    slot_teams: list[int]
    per_slot_account_ids: list[int]
    host_account_id: int
    game_mode: int
    win_condition: int
    team_type: int
    freemods_enabled: bool
    per_slot_mods: list[int]
    random_seed: int


class OsuScoreFrame(TypedDict):
    time: int
    id: int
    num_300s: int
    num_100s: int
    num_50s: int
    num_gekis: int
    num_katus: int
    num_misses: int
    total_score: int
    current_combo: int
    max_combo: int
    perfect: bool
    current_hp: int
    tag_byte: int
    score_v2: bool

    # only required for scorev2
    combo_portion: NotRequired[float]
    bonus_portion: NotRequired[float]


class OsuReplayFrame(TypedDict):
    button_state: int
    taiko_byte: int  # pre-taiko support (<=2008)
    x: float
    y: float
    time: int


class ReplayAction:
    STANDARD = 0
    NEW_SONG = 1
    SKIP = 2
    COMPLETION = 3
    FAIL = 4
    PAUSE = 5
    UNPAUSE = 6
    SONG_SELECT = 7
    WATCHING_OTHER = 8


class OsuReplayFrameBundle(TypedDict):
    replay_frames: list[OsuReplayFrame]
    score_frame: OsuScoreFrame
    replay_action: int  # ReplayAction
    extra: int
    sequence_number: int


class PacketReader:
    def __init__(self, data: bytes) -> None:
        self.data_view = memoryview(data)

    def read(self, num_bytes: int) -> bytes:
        data = self.data_view[:num_bytes]
        self.data_view = self.data_view[num_bytes:]
        return data.tobytes()  # copy on exit

    # primitive data types

    def read_i8(self) -> int:
        return struct.unpack("<b", self.read(1))[0]

    def read_u8(self) -> int:
        return struct.unpack("<B", self.read(1))[0]

    def read_i16(self) -> int:
        return struct.unpack("<h", self.read(2))[0]

    def read_u16(self) -> int:
        return struct.unpack("<H", self.read(2))[0]

    def read_i32(self) -> int:
        return struct.unpack("<i", self.read(4))[0]

    def read_u32(self) -> int:
        return struct.unpack("<I", self.read(4))[0]

    def read_i64(self) -> int:
        return struct.unpack("<q", self.read(8))[0]

    def read_u64(self) -> int:
        return struct.unpack("<Q", self.read(8))[0]

    def read_f32(self) -> float:
        return struct.unpack("<f", self.read(4))[0]

    def read_f64(self) -> float:
        return struct.unpack("<d", self.read(8))[0]

    # more complex data types

    def read_uleb128(self) -> int:
        value = 0
        shift = 0
        while True:
            byte = self.read_u8()
            value |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                break
        return value

    def read_string(self) -> str:
        if self.read(1) != b"\x0b":
            return ""
        length = self.read_uleb128()
        return self.read(length).decode()

    def read_i32_list_i16_length(self) -> list[int]:
        return [self.read_i32() for _ in range(self.read_i16())]

    def read_i32_list_i32_length(self) -> list[int]:
        return [self.read_i32() for _ in range(self.read_i32())]

    # osu! specific data types

    def read_osu_message(self) -> OsuMessage:
        return {
            "sender_name": self.read_string(),  # always ""
            "message_content": self.read_string(),
            "recipient_name": self.read_string(),
            "sender_id": self.read_i32(),  # always 0
        }

    def read_osu_channel(self) -> OsuChannel:
        return {
            "channel_name": self.read_string(),
            "channel_topic": self.read_string(),
            "channel_user_count": self.read_i16(),
        }

    def read_osu_match(self) -> OsuMatch:
        match_id = self.read_i16()  # match id
        match_in_progress = self.read_i8() == 1  # in_progress
        _ = self.read_i8()  # powerplay
        mods = self.read_i32()  # mods
        match_name = self.read_string()
        match_password = self.read_string()
        beatmap_name = self.read_string()
        beatmap_id = self.read_i32()
        beatmap_md5 = self.read_string()
        slot_statuses = [self.read_i8() for _ in range(16)]
        slot_teams = [self.read_i8() for _ in range(16)]
        # ^^ up to slot_ids, as it relies on slot_statuses ^^

        per_slot_account_ids = []
        for status in slot_statuses:
            if status & 0b01111100 != 0:  # slot has a player
                per_slot_account_ids.append(self.read_i32())

        host_account_id = self.read_i32()
        game_mode = self.read_i8()
        win_condition = self.read_i8()
        team_type = self.read_i8()
        freemods_enabled = self.read_i8() == 1

        if freemods_enabled:
            per_slot_mods = [self.read_i32() for _ in range(16)]
        else:
            per_slot_mods = []

        random_seed = self.read_i32()  # used for mania random mod

        return {
            "match_id": match_id,
            "match_in_progress": match_in_progress,
            "mods": mods,
            "match_name": match_name,
            "match_password": match_password,
            "beatmap_name": beatmap_name,
            "beatmap_id": beatmap_id,
            "beatmap_md5": beatmap_md5,
            "slot_statuses": slot_statuses,
            "slot_teams": slot_teams,
            "per_slot_account_ids": per_slot_account_ids,
            "host_account_id": host_account_id,
            "game_mode": game_mode,
            "win_condition": win_condition,
            "team_type": team_type,
            "freemods_enabled": freemods_enabled,
            "per_slot_mods": per_slot_mods,
            "random_seed": random_seed,
        }

    def read_osu_score_frame(self) -> OsuScoreFrame:
        rec: OsuScoreFrame = {
            "time": self.read_i32(),
            "id": self.read_u8(),
            "num_300s": self.read_u16(),
            "num_100s": self.read_u16(),
            "num_50s": self.read_u16(),
            "num_gekis": self.read_u16(),
            "num_katus": self.read_u16(),
            "num_misses": self.read_u16(),
            "total_score": self.read_i32(),
            "current_combo": self.read_u16(),
            "max_combo": self.read_u16(),
            "perfect": self.read_u8() == 1,
            "current_hp": self.read_u8(),
            "tag_byte": self.read_u8(),
            "score_v2": self.read_u8() == 1,
        }
        if rec["score_v2"]:
            rec["combo_portion"] = self.read_f64()
            rec["bonus_portion"] = self.read_f64()

        return rec

    def read_osu_replay_frame(self) -> OsuReplayFrame:
        return {
            "button_state": self.read_u8(),
            "taiko_byte": self.read_u8(),  # pre-taiko support (<=2008)
            "x": self.read_f32(),
            "y": self.read_f32(),
            "time": self.read_i32(),
        }

    def read_replay_frame_bundle(self) -> OsuReplayFrameBundle:
        extra = self.read_i32()  # bancho proto >= 18
        replay_frame_count = self.read_u16()
        replay_frames = [
            self.read_osu_replay_frame() for _ in range(replay_frame_count)
        ]
        replay_action = self.read_u8()
        score_frame = self.read_osu_score_frame()
        sequence_number = self.read_u16()

        return {
            "replay_frames": replay_frames,
            "score_frame": score_frame,
            "replay_action": replay_action,
            "extra": extra,
            "sequence_number": sequence_number,
        }


def read_packets(request_data: bytes) -> list[Packet]:
    packets = []
    offset = 0
    while request_data[offset:]:
        packet_id, packet_len = struct.unpack("<HxL", request_data[offset : offset + 7])
        offset += 7

        packet_data = request_data[offset : offset + packet_len]
        assert len(packet_data) == packet_len, "packet data shorter than expected"
        offset += packet_len

        packet = Packet(packet_id, packet_len, packet_data)
        packets.append(packet)

    return packets


class DataType(Enum):
    # primitive types
    I8 = "i8"
    U8 = "u8"
    I16 = "i16"
    U16 = "u16"
    I32 = "i32"
    U32 = "u32"
    I64 = "i64"
    U64 = "u64"
    F32 = "f32"
    F64 = "f64"

    # "advanced" types
    I32_LIST_I16_LEN = "i32_list_i16_len"  # 2 bytes len
    I32_LIST_I32_LEN = "i32_list_i32_len"  # 4 bytes len
    STRING = "string"
    RAW_DATA = "raw_data"

    # high level osu-specific types
    OSU_MESSAGE = "osu_message"
    OSU_CHANNEL = "osu_channel"
    OSU_MATCH = "osu_match"
    OSU_SCOREFRAME = "osu_scoreframe"
    OSU_MAP_INFO_REQUEST = "osu_map_info_request"
    OSU_MAP_INFO_REPLY = "osu_map_info_reply"
    OSU_REPLAY_FRAME_BUNDLE = "osu_replay_frame_bundle"


def write_uleb128(value: int) -> bytes:
    data = bytearray()
    while value != 0:
        data.append(value & 0x7F)
        value >>= 7
        if value != 0:
            data[-1] |= 0x80

    return data


def write_string(value: str) -> bytes:
    if len(value) == 0:
        return b"\x00"
    else:
        encoded = value.encode()
        return b"\x0b" + write_uleb128(len(encoded)) + encoded


# osu! specific data types


def write_i32_list_i16_len(values: list[int]) -> bytes:
    encoded_len = struct.pack("<H", len(values))
    for value in values:
        encoded_len += struct.pack("<i", value)
    return encoded_len


def write_osu_message(value: OsuMessage) -> bytes:
    return (
        write_string(value["sender_name"])
        + write_string(value["message_content"])
        + write_string(value["recipient_name"])
        + struct.pack("<i", value["sender_id"])
    )


def write_osu_match(
    match_data: OsuMatch,
    should_send_password: bool = False,
) -> bytes:
    buffer = bytearray()
    buffer += struct.pack("<H", match_data["match_id"])
    buffer += struct.pack("<B", match_data["match_in_progress"])
    buffer += struct.pack("<B", 0)  # powerplay
    buffer += struct.pack("<I", match_data["mods"])
    buffer += write_string(match_data["match_name"])
    if match_data["match_password"]:
        if should_send_password:
            buffer += write_string(match_data["match_password"])
        else:
            # hidden password: "\x0b\x00"
            buffer += b"\x0b\x00"
    else:
        # no password: "\x00"
        buffer += b"\x00"
    buffer += write_string(match_data["beatmap_name"])
    buffer += struct.pack("<i", match_data["beatmap_id"])
    buffer += write_string(match_data["beatmap_md5"])
    buffer += struct.pack("<16b", *match_data["slot_statuses"])
    buffer += struct.pack("<16b", *match_data["slot_teams"])
    buffer += struct.pack(
        f"<{len(match_data['per_slot_account_ids'])}I",
        *match_data["per_slot_account_ids"],
    )
    buffer += struct.pack("<I", match_data["host_account_id"])
    buffer += struct.pack("<B", match_data["game_mode"])
    buffer += struct.pack("<B", match_data["win_condition"])
    buffer += struct.pack("<B", match_data["team_type"])
    buffer += struct.pack("<B", match_data["freemods_enabled"])
    if match_data["freemods_enabled"]:
        buffer += struct.pack(
            f"<{len(match_data['per_slot_mods'])}i", *match_data["per_slot_mods"]
        )
    buffer += struct.pack("<i", match_data["random_seed"])
    return bytes(buffer)


def write_osu_score_frame(score_frame: OsuScoreFrame) -> bytes:
    buffer = bytearray()
    buffer += struct.pack("<i", score_frame["time"])
    buffer += struct.pack("<B", score_frame["id"])
    buffer += struct.pack("<H", score_frame["num_300s"])
    buffer += struct.pack("<H", score_frame["num_100s"])
    buffer += struct.pack("<H", score_frame["num_50s"])
    buffer += struct.pack("<H", score_frame["num_gekis"])
    buffer += struct.pack("<H", score_frame["num_katus"])
    buffer += struct.pack("<H", score_frame["num_misses"])
    buffer += struct.pack("<i", score_frame["total_score"])
    buffer += struct.pack("<H", score_frame["current_combo"])
    buffer += struct.pack("<H", score_frame["max_combo"])
    buffer += struct.pack("<B", score_frame["perfect"])
    buffer += struct.pack("<B", score_frame["current_hp"])
    buffer += struct.pack("<B", score_frame["tag_byte"])
    buffer += struct.pack("<B", score_frame["score_v2"])
    if score_frame["score_v2"]:
        assert "combo_portion" in score_frame
        assert "bonus_portion" in score_frame
        buffer += struct.pack("<d", score_frame["combo_portion"])
        buffer += struct.pack("<d", score_frame["bonus_portion"])
    return bytes(buffer)


def write_osu_replay_frame(replay_frame: OsuReplayFrame) -> bytes:
    buffer = bytearray()
    buffer += struct.pack("<B", replay_frame["button_state"])
    buffer += struct.pack("<B", replay_frame["taiko_byte"])
    buffer += struct.pack("<f", replay_frame["x"])
    buffer += struct.pack("<f", replay_frame["y"])
    buffer += struct.pack("<i", replay_frame["time"])
    return bytes(buffer)


def write_replay_frame_bundle(replay_frame_bundle: OsuReplayFrameBundle) -> bytes:
    buffer = bytearray()
    buffer += struct.pack("<i", 0)  # extra
    buffer += struct.pack("<H", len(replay_frame_bundle["replay_frames"]))
    for frame in replay_frame_bundle["replay_frames"]:
        buffer += write_osu_replay_frame(frame)
    buffer += struct.pack("<B", replay_frame_bundle["replay_action"])
    buffer += write_osu_score_frame(replay_frame_bundle["score_frame"])
    buffer += struct.pack("<H", replay_frame_bundle["sequence_number"])
    return bytes(buffer)


def write_packet(
    packet_id: int,
    packet_data_inputs: list[tuple[DataType, Any]],
) -> bytes:
    # packet data
    packet_body = b""

    # TODO: create data out of packet_data_inputs
    for type, value in packet_data_inputs:
        if type == DataType.I8:
            packet_body += struct.pack("<b", value)
        elif type == DataType.I16:
            packet_body += struct.pack("<h", value)
        elif type == DataType.I32:
            packet_body += struct.pack("<i", value)
        elif type == DataType.I64:
            packet_body += struct.pack("<q", value)
        elif type == DataType.U8:
            packet_body += struct.pack("<B", value)
        elif type == DataType.U16:
            packet_body += struct.pack("<H", value)
        elif type == DataType.U32:
            packet_body += struct.pack("<I", value)
        elif type == DataType.U64:
            packet_body += struct.pack("<Q", value)
        elif type == DataType.F32:
            packet_body += struct.pack("<f", value)
        elif type == DataType.F64:
            packet_body += struct.pack("<d", value)
        elif type == DataType.STRING:
            packet_body += write_string(value)
        elif type == DataType.I32_LIST_I16_LEN:
            packet_body += write_i32_list_i16_len(value)
        elif type == DataType.OSU_MESSAGE:
            packet_body += write_osu_message(value)
        elif type == DataType.OSU_MATCH:
            packet_body += write_osu_match(*value)
        elif type == DataType.OSU_SCOREFRAME:
            packet_body += write_osu_score_frame(value)
        elif type == DataType.OSU_REPLAY_FRAME_BUNDLE:
            packet_body += write_replay_frame_bundle(value)
        elif type == DataType.RAW_DATA:
            packet_body += value
        else:
            raise RuntimeError("Unknown packet type")

    # packet header
    packet_header = struct.pack("<HxL", packet_id, len(packet_body))

    return packet_header + packet_body


# USER_ID = 5


def write_user_id_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.USER_ID,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# SEND_MESSAGE = 7


def write_send_message_packet(
    sender_name: str,
    message_content: str,
    recipient_name: str,
    sender_id: int,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.SEND_MESSAGE,
        packet_data_inputs=[
            (DataType.STRING, sender_name),
            (DataType.STRING, message_content),
            (DataType.STRING, recipient_name),
            (DataType.I32, sender_id),
        ],
    )


# PONG = 8


# HANDLE_IRC_CHANGE_USERNAME = 9  # unused


# HANDLE_IRC_QUIT = 10


# USER_STATS = 11


def write_user_stats_packet(
    account_id: int,
    action: int,
    info_text: str,
    beatmap_md5: str,
    mods: int,
    game_mode: int,
    beatmap_id: int,
    ranked_score: int,
    accuracy: float,
    play_count: int,
    total_score: int,
    global_rank: int,
    performance_points: int,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.USER_STATS,
        packet_data_inputs=[
            (DataType.I32, account_id),
            (DataType.U8, action),
            (DataType.STRING, info_text),
            (DataType.STRING, beatmap_md5),
            (DataType.I32, mods),
            (DataType.U8, game_mode),
            (DataType.I32, beatmap_id),
            (DataType.I64, ranked_score),
            (DataType.F32, accuracy / 100.0),
            (DataType.I32, play_count),
            (DataType.I64, total_score),
            (DataType.I32, global_rank),
            (DataType.I16, performance_points),
        ],
    )


# USER_LOGOUT = 12


def write_logout_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.USER_LOGOUT,
        packet_data_inputs=[
            (DataType.I32, user_id),
            (DataType.U8, 0),
        ],
    )


# SPECTATOR_JOINED = 13


def write_spectator_joined_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.SPECTATOR_JOINED,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# SPECTATOR_LEFT = 14


def write_spectator_left_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.SPECTATOR_LEFT,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# SPECTATE_FRAMES = 15


def write_spectate_frames_packet(replay_frame_bundle: OsuReplayFrameBundle) -> bytes:
    return write_packet(
        packet_id=ServerPackets.SPECTATE_FRAMES,
        packet_data_inputs=[
            (DataType.OSU_REPLAY_FRAME_BUNDLE, replay_frame_bundle),
        ],
    )


# VERSION_UPDATE = 19


# SPECTATOR_CANT_SPECTATE = 22


def write_spectator_cant_spectate_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.SPECTATOR_CANT_SPECTATE,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# GET_ATTENTION = 23


# NOTIFICATION = 24


def write_notification_packet(
    message: str,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.NOTIFICATION,
        packet_data_inputs=[
            (DataType.STRING, message),
        ],
    )


# UPDATE_MATCH = 26


def write_update_match_packet(
    match_data: OsuMatch,
    should_send_password: bool,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.UPDATE_MATCH,
        packet_data_inputs=[
            (DataType.OSU_MATCH, (match_data, should_send_password)),
        ],
    )


# NEW_MATCH = 27


def write_new_match_packet(match_data: OsuMatch) -> bytes:
    return write_packet(
        packet_id=ServerPackets.NEW_MATCH,
        packet_data_inputs=[
            (DataType.OSU_MATCH, match_data),
        ],
    )


# DISPOSE_MATCH = 28


def write_dispose_match_packet(match_id: int) -> bytes:
    return write_packet(
        ServerPackets.DISPOSE_MATCH,
        packet_data_inputs=[
            (DataType.I32, match_id),
        ],
    )


# TOGGLE_BLOCK_NON_FRIEND_DMS = 34


# MATCH_JOIN_SUCCESS = 36


def write_match_join_success_packet(
    match_data: OsuMatch,
    should_send_password: bool,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_JOIN_SUCCESS,
        packet_data_inputs=[
            (DataType.OSU_MATCH, (match_data, should_send_password)),
        ],
    )


# MATCH_JOIN_FAIL = 37


def write_match_join_fail_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_JOIN_FAIL,
        packet_data_inputs=[],
    )


# FELLOW_SPECTATOR_JOINED = 42


def write_fellow_spectator_joined_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.FELLOW_SPECTATOR_JOINED,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# FELLOW_SPECTATOR_LEFT = 43


def write_fellow_spectator_left_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.FELLOW_SPECTATOR_LEFT,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# ALL_PLAYERS_LOADED = 45


# MATCH_START = 46


def write_match_start_packet(
    match_data: OsuMatch,
    should_send_password: bool,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_START,
        packet_data_inputs=[
            (DataType.OSU_MATCH, (match_data, should_send_password)),
        ],
    )


# MATCH_SCORE_UPDATE = 48


def write_match_score_update_packet(data: bytes) -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_SCORE_UPDATE,
        packet_data_inputs=[
            (DataType.RAW_DATA, data),
        ],
    )


# MATCH_TRANSFER_HOST = 50


def write_match_transfer_host_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_TRANSFER_HOST,
        packet_data_inputs=[],
    )


# MATCH_ALL_PLAYERS_LOADED = 53


def write_match_all_players_loaded_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_ALL_PLAYERS_LOADED,
        packet_data_inputs=[],
    )


# MATCH_PLAYER_FAILED = 57


def write_match_player_failed_packet(slot_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_PLAYER_FAILED,
        packet_data_inputs=[
            (DataType.I32, slot_id),
        ],
    )


# MATCH_COMPLETE = 58


def write_match_complete_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_COMPLETE,
        packet_data_inputs=[],
    )


# MATCH_SKIP = 61


def write_match_skip_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_SKIP,
        packet_data_inputs=[],
    )


# UNAUTHORIZED = 62  # unused


# CHANNEL_JOIN_SUCCESS = 64


def write_channel_join_success_packet(channel_name: str) -> bytes:
    return write_packet(
        packet_id=ServerPackets.CHANNEL_JOIN_SUCCESS,
        packet_data_inputs=[(DataType.STRING, channel_name)],
    )


# CHANNEL_INFO = 65


def write_channel_info_packet(
    name: str,
    topic: str,
    num_sessions: int,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.CHANNEL_INFO,
        packet_data_inputs=[
            (DataType.STRING, name),
            (DataType.STRING, topic),
            (DataType.U16, num_sessions),
        ],
    )


# CHANNEL_KICK = 66


def write_channel_kick_packet(channel_name: str) -> bytes:
    return write_packet(
        packet_id=ServerPackets.CHANNEL_KICK,
        packet_data_inputs=[
            (DataType.STRING, channel_name),
        ],
    )


# CHANNEL_AUTO_JOIN = 67


def write_channel_auto_join_packet(
    name: str,
    topic: str,
    session_count: int,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.CHANNEL_AUTO_JOIN,
        packet_data_inputs=[
            (DataType.STRING, name),
            (DataType.STRING, topic),
            (DataType.U16, session_count),
        ],
    )


# BEATMAP_INFO_REPLY = 69


# PRIVILEGES = 71


def write_user_privileges_packet(privileges: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.PRIVILEGES,
        packet_data_inputs=[(DataType.I32, privileges)],
    )


# FRIENDS_LIST = 72


def write_friends_list_packet(user_ids: list[int]) -> bytes:
    return write_packet(
        packet_id=ServerPackets.FRIENDS_LIST,
        packet_data_inputs=[(DataType.I32_LIST_I16_LEN, user_ids)],
    )


# PROTOCOL_VERSION = 75


def write_protocol_version_packet(version: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.PROTOCOL_VERSION,
        packet_data_inputs=[(DataType.I32, version)],
    )


# MAIN_MENU_ICON = 76


# MONITOR = 80  # unused


# MATCH_PLAYER_SKIPPED = 81


def write_match_player_skipped_packet(slot_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.MATCH_PLAYER_SKIPPED,
        packet_data_inputs=[(DataType.I32, slot_id)],
    )


# USER_PRESENCE = 83


def write_user_presence_packet(
    account_id: int,
    username: str,
    utc_offset: int,
    country: int,
    privileges: int,
    game_mode: int,
    latitude: int,
    longitude: int,
    global_rank: int,
) -> bytes:
    return write_packet(
        packet_id=ServerPackets.USER_PRESENCE,
        packet_data_inputs=[
            (DataType.I32, account_id),
            (DataType.STRING, username),
            (DataType.U8, utc_offset + 24),
            (DataType.U8, country),
            (DataType.U8, privileges | (game_mode << 5)),
            (DataType.F32, longitude),
            (DataType.F32, latitude),
            (DataType.I32, global_rank),
        ],
    )


# RESTART = 86


def write_restart_packet(millseconds_until_restart: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.RESTART,
        packet_data_inputs=[(DataType.I32, millseconds_until_restart)],
    )


# MATCH_INVITE = 88


# CHANNEL_INFO_END = 89


def write_channel_listing_complete_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.CHANNEL_INFO_END,
        packet_data_inputs=[],
    )


# MATCH_CHANGE_PASSWORD = 91


# SILENCE_END = 92


def write_silence_end_packet(seconds_remaining: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.SILENCE_END,
        packet_data_inputs=[(DataType.I32, seconds_remaining)],
    )


# USER_SILENCED = 94


def write_user_silenced_packet(user_id: int) -> bytes:
    return write_packet(
        packet_id=ServerPackets.USER_SILENCED,
        packet_data_inputs=[(DataType.I32, user_id)],
    )


# USER_PRESENCE_SINGLE = 95


# USER_PRESENCE_BUNDLE = 96


# USER_DM_BLOCKED = 100


def write_user_dm_blocked_packet(username: str) -> bytes:
    message = OsuMessage(
        sender_name="",
        sender_id=0,
        message_content="",
        recipient_name=username,
    )
    return write_packet(
        packet_id=ServerPackets.USER_DM_BLOCKED,
        packet_data_inputs=[(DataType.OSU_MESSAGE, message)],
    )


# TARGET_IS_SILENCED = 101


def write_target_is_silenced_packet(username: str) -> bytes:
    message = OsuMessage(
        sender_name="",
        sender_id=0,
        message_content="",
        recipient_name=username,
    )
    return write_packet(
        packet_id=ServerPackets.TARGET_IS_SILENCED,
        packet_data_inputs=[(DataType.OSU_MESSAGE, message)],
    )


# VERSION_UPDATE_FORCED = 102


# SWITCH_SERVER = 103


# ACCOUNT_RESTRICTED = 104


def write_account_restricted_packet() -> bytes:
    return write_packet(
        packet_id=ServerPackets.ACCOUNT_RESTRICTED,
        packet_data_inputs=[],
    )


# RTX = 105  # unused


# MATCH_ABORT = 106


# SWITCH_TOURNAMENT_SERVER = 107
