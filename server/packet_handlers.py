from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING

from server import logger
from server import packets
from server.repositories import packet_bundles
from server.repositories import sessions

if TYPE_CHECKING:
    from server.repositories.sessions import Session

packet_handlers = {}


def get_packet_handler(packet_id: packets.ClientPackets):
    return packet_handlers.get(packet_id)


BanchoHandler = Callable[["Session", bytes], Awaitable[None]]


def bancho_handler(
    packet_id: packets.ClientPackets,
) -> Callable[[BanchoHandler], BanchoHandler]:
    def wrapper(f: BanchoHandler) -> BanchoHandler:
        packet_handlers[packet_id] = f
        return f

    return wrapper


@bancho_handler(packets.ClientPackets.LOGOUT)
async def logout_handler(session: "Session", packet_data: bytes) -> None:
    await sessions.delete_by_id(session["session_id"])

    # tell everyone else we logged out
    logout_packet_data = packets.write_logout_packet(session["account_id"])
    for other_session in await sessions.fetch_all():
        await packet_bundles.enqueue(
            other_session["session_id"],
            data=logout_packet_data,
        )

    logger.info(
        "Log out successful",
        session_id=session["session_id"],
        account_id=session["account_id"],
    )


@bancho_handler(packets.ClientPackets.PING)
async def ping_handler(session: "Session", packet_data: bytes):
    # TODO: keep track of each osu! session's last ping time
    pass


@bancho_handler(packets.ClientPackets.SEND_PUBLIC_MESSAGE)
async def send_public_message_handler(session: "Session", packet_data: bytes):
    # read packet data
    packet_reader = packets.PacketReader(packet_data)

    sender_name = packet_reader.read_string()
    message_content = packet_reader.read_string()
    recipient_name = packet_reader.read_string()
    sender_id = packet_reader.read_i32()

    # send message to everyone else
    send_message_packet_data = packets.write_send_message_packet(
        sender_name, message_content, recipient_name, sender_id
    )

    for other_session in await sessions.fetch_all(osu_clients_only=True):
        if other_session["session_id"] == session["session_id"]:
            continue

        await packet_bundles.enqueue(
            other_session["session_id"],
            data=send_message_packet_data,
        )
