import logging
import socket
import struct
from typing import Iterable, Tuple

from bounce_rl.x_proxy import anc_data_util, x_overrides

GENERIC_EVENT_CODE = 35


class ReplyStream:
    def __init__(
        self, socket: socket.socket, request_codes: dict[int, int], conn_id: int
    ):
        self.socket = socket
        self.end = 0
        self.queued_bytes = bytearray()
        self.connected = False
        self.request_codes = request_codes
        self.conn_id = conn_id

        self.reply_handlers = x_overrides.ReplyHandlerTable()
        self.event_handlers = x_overrides.EventHandlerTable()

    def _take_from_queue(self, n: int) -> memoryview:
        v = memoryview(self.queued_bytes)[self.end : self.end + n]
        self.end += n
        return v

    def _remaining_bytes(self) -> int:
        return len(self.queued_bytes) - self.end

    def _replace_last_message(self, msg_len: int, new_msg: bytes) -> None:
        logging.debug("Replacing last reply")
        self.queued_bytes = (
            self.queued_bytes[: self.end - msg_len]
            + new_msg
            + self.queued_bytes[self.end :]
        )
        self.end = self.end - msg_len + len(new_msg)

    def _handle_connection(self) -> None:
        n = len(self.queued_bytes)
        if n < 8:
            return
        code, major, minor, additional_data_len = struct.unpack(
            "BxHHH", self.queued_bytes[:8]
        )
        assert code == 1, "Client received unexpected connection code " + str(code)
        total_len = 8 + additional_data_len * 4
        if n >= total_len:
            logging.info("Client finished setup")
            self.end += total_len
            self.connected = True

    def consume(self, data: bytearray, anc_data: Tuple):
        logging.debug("Consuming %d reply bytes", len(data))

        self.queued_bytes += data
        if not self.connected:
            self._handle_connection()

        while self.connected and len(self.queued_bytes) - self.end >= 32:
            code, detail, sequence_num, extra_length = struct.unpack(
                "BBHI", self.queued_bytes[self.end : self.end + 8]
            )
            is_event = code > 1
            is_reply = code == 1
            is_error = code == 0

            logging.debug(
                "Reply conn %d, serial %d, code %d, extra_len %d, remaining %d",
                self.conn_id,
                sequence_num,
                code,
                extra_length,
                self._remaining_bytes(),
            )

            if is_error:
                logging.info(f"X11 Error: {code}")
                self._take_from_queue(32)
            elif is_reply:
                msg_len = 32 + 4 * extra_length
                if self._remaining_bytes() < msg_len:
                    break

                opcode = self.request_codes.get(sequence_num, -1)
                reply = self._take_from_queue(msg_len)
                if opcode in self.reply_handlers:
                    new_reply = self.reply_handlers[opcode](reply)
                    if new_reply is not None:
                        self._replace_last_message(msg_len, new_reply)
            elif is_event:
                if code != GENERIC_EVENT_CODE:
                    extra_length = 0
                msg_len = 32 + 4 * extra_length

                # Unset the send event bit.
                self.queued_bytes[0] &= 0x7F

                if self._remaining_bytes() < msg_len:
                    break

                event = self._take_from_queue(msg_len)
                if code in self.event_handlers:
                    should_filter = self.event_handlers[code](event)
                    if should_filter:
                        self._replace_last_message(msg_len, b"")

        logging.debug("Initial %d reply bytes", len(self.queued_bytes))
        logging.debug("Sending out %d reply bytes", self.end)
        logging.debug("Remaining reply bytes: %d", len(self.queued_bytes) - self.end)
        to_send = memoryview(self.queued_bytes)[: self.end]
        self.socket.sendmsg([to_send], anc_data)
        self.queued_bytes = self.queued_bytes[self.end :]
        self.end = 0


class ReplyConnection:
    def __init__(
        self, socket: socket.socket, request_codes: dict[int, int], conn_id: int
    ):
        self.socket = socket
        self.reply_stream = ReplyStream(socket, request_codes, conn_id)

    def sendmsg(self, buffers: Iterable[bytearray], anc_data: Tuple):
        buffer = bytearray()
        for buf in buffers:
            buffer += buf
        self.reply_stream.consume(buffer, anc_data)
        anc_data_util.cleanup_anc_data(anc_data)

    def get_socket(self) -> socket.socket:
        return self.reply_stream.socket
