import logging
import socket
import struct
from typing import Iterable, Tuple

from bounce_rl.x_proxy import anc_data_util, server_state


def pad(n: int) -> int:
    return n + (4 - (n % 4)) % 4


class RequestStream:
    def __init__(
        self,
        socket: socket.socket,
        conn_id: int,
        server_state: server_state.ServerState,
    ):
        self.socket = socket
        self.end = 0
        self.queued_bytes = bytearray()
        self.connected = False
        self.request_codes = {}
        self.serial = 3
        self.conn_id = conn_id
        self.server_state = server_state

        # Deferred import to avoid circular dependency.
        from bounce_rl.x_proxy import x_overrides

        self.request_handlers = x_overrides.request_handler_table()

    def _take_from_queue(self, n: int) -> memoryview:
        v = memoryview(self.queued_bytes)[self.end : self.end + n]
        self.end += n
        return v

    def _replace_last_message(self, msg_len: int, new_msg: bytes) -> None:
        self.queued_bytes = (
            self.queued_bytes[: self.end - msg_len]
            + new_msg
            + self.queued_bytes[self.end :]
        )
        self.end = self.end - msg_len + len(new_msg)

    def _remaining_bytes(self) -> int:
        return len(self.queued_bytes) - self.end

    def _handle_connection(self) -> None:
        n = len(self.queued_bytes)
        if n < 12:
            return
        endianess, major, minor, n_0, n_1 = struct.unpack(
            "BxHHHH", self.queued_bytes[:10]
        )
        is_little_endian = chr(endianess) == "l"
        assert is_little_endian, "XProxy only supports little endian connections"

        n = 12 + pad(n_0) + pad(n_1)
        if len(self.queued_bytes) >= n:
            self.end += n
            self.connected = True
            self.serial += 1

    def consume(self, data: bytearray, anc_data: Tuple) -> None:
        logging.debug("Consuming %d request bytes", len(data))

        self.queued_bytes += data

        if not self.connected:
            self._handle_connection()

        while self.connected and len(self.queued_bytes) - self.end >= 4:
            opcode, request_len = struct.unpack(
                "BxH", self.queued_bytes[self.end : self.end + 4]
            )
            logging.debug("Request opcode %d, serial %d", opcode, self.serial)
            if request_len == 0:
                # Big request protocol request
                request_len = struct.unpack(
                    "I", self.queued_bytes[self.end + 4 : self.end + 8]
                )[0]
            msg_len = 4 * request_len

            if self._remaining_bytes() < msg_len:
                break

            logging.debug(
                f"Queue size: {len(self.queued_bytes)}, request bytes: {msg_len}"
            )
            if len(self.queued_bytes) < msg_len:
                self.fallback_n += 1
                if self.fallback_n > 70:
                    self.queued_bytes = bytearray()
                    self.fallback_n = 0
                logging.warning(
                    f"Request parsing hit error heuristic. Fallback val: {self.fallback_n}"
                )
                return

            request = self._take_from_queue(msg_len)
            self.request_codes[self.serial] = opcode
            self.serial = (self.serial + 1) % 2**16
            if opcode in self.request_handlers:
                new_request = self.request_handlers[opcode](request, self)
                if new_request is not None:
                    logging.debug(
                        "Replacing request message orig len: %d, new len: %d",
                        msg_len,
                        len(new_request),
                    )
                    self._replace_last_message(msg_len, new_request)

        logging.debug("Sending out %d request bytes", self.end)
        to_send = memoryview(self.queued_bytes)[: self.end]
        self.socket.sendmsg([to_send], anc_data)
        self.queued_bytes = self.queued_bytes[self.end :]
        self.end = 0


class RequestConnection:
    def __init__(
        self,
        socket: socket.socket,
        conn_id: int,
        server_state: server_state.ServerState,
    ):
        self.socket = socket
        self.request_stream = RequestStream(socket, conn_id, server_state)

    def sendmsg(self, buffers: Iterable[bytearray], anc_data: Tuple):
        buffer = bytearray()
        for buf in buffers:
            buffer += buf
        self.request_stream.consume(buffer, anc_data)
        anc_data_util.cleanup_anc_data(anc_data)

    def get_socket(self) -> socket.socket:
        return self.request_stream.socket
