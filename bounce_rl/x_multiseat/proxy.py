# Proxies a new X11 display to an existing one, while setting override-redirect to
# true on all windows created on the new display.
#
# To run an app through the proxy, start the proxy server with
#   $ python proxy.py
# Then run the client app with
#   $ DISPLAY=:1 app
#
# If you get any errors about authentication, setup X authentication on display 1 by
# first installing xauth and then running
#   $ xauth list
# and then coping the long hex string printed and running
#   $ xauth add :1 . $HEX_STRING

import argparse
import atexit
import logging
import os
import select
import signal
import socket
import struct
import sys
from typing import Iterable, Set

logging.basicConfig(level=logging.WARNING)

# Global first constructed XMessageStream. This is used by main to get the server
# timestamp.
first_stream = None

CREATE_WINDOW = 1
CHANGE_WINDOW_ATTRIBUTES = 2

FOCUS_IN = 9
FOCUS_OUT = 10
LAST_STANDARD_EVENT = 34
GENERIC_EVENT_CODE = 35

OVERRIDE_REDIRECT = 0x00000200


def pad(n):
    return n + (4 - (n % 4)) % 4


class RequestParser:
    def __init__(self, socket: socket.socket, request_codes: dict):
        self.socket = socket
        self.is_connected = False
        self.queued_bytes = bytearray()
        self.fallback_n = 0
        self.serial = 3
        self.request_codes = request_codes

    def send(self, n: int):
        self.socket.sendmsg([self.queued_bytes[:n]])
        self.queued_bytes = self.queued_bytes[n:]

    def consume(self, data: bytes):
        global request_codes
        self.queued_bytes += data

        while True:
            n = len(self.queued_bytes)
            if not self.is_connected:
                if n < 12:
                    return
                endianess, major, minor, n_0, n_1 = struct.unpack(
                    "BxHHHH", self.queued_bytes[:10]
                )
                is_little_endian = chr(endianess) == "l"
                assert (
                    is_little_endian
                ), "XProxy only supports little endian connections"

                n = 12 + pad(n_0) + pad(n_1)
                if len(self.queued_bytes) < n:
                    return
                self.serial += 1
                self.send(n)
                self.is_connected = True
                continue

            if n < 4:
                return

            opcode, request_len = struct.unpack("BxH", self.queued_bytes[:4])
            # Big request protocol.
            if request_len == 0:
                request_len = struct.unpack("I", self.queued_bytes[4:8])[0]

            request_bytes = 4 * request_len
            logging.debug(
                f"Queue size: {len(self.queued_bytes)}, request bytes: {request_bytes}"
            )
            if len(self.queued_bytes) < request_bytes:
                self.fallback_n += 1
                if self.fallback_n > 70:
                    self.queued_bytes = bytearray()
                    self.fallback_n = 0
                logging.warning(
                    f"Request parsing hit error heuristic. Fallback val: {self.fallback_n}"
                )
                return

            # Force override redirect on CreateWindow calls.
            if opcode == CREATE_WINDOW:
                logging.debug("Overriding redirect on created window!")
                # Add the override redirect attribute.
                orig_mask = struct.unpack("I", self.queued_bytes[28:32])[0]
                new_mask = orig_mask | OVERRIDE_REDIRECT
                built_message = self.queued_bytes[0:32]
                next_val = 0
                for i in range(32):
                    bit_mask = 1 << i
                    if new_mask & bit_mask:
                        if bit_mask != OVERRIDE_REDIRECT:
                            built_message += self.queued_bytes[
                                32 + 4 * next_val : 32 + 4 * (next_val + 1)
                            ]
                            next_val += 1
                        else:
                            # Should this be Bxxx or I? Given that this
                            # is little endian, it shouldn't matter.
                            built_message += struct.pack("Bxxx", 1)
                            if orig_mask & OVERRIDE_REDIRECT:
                                next_val += 1
                orig_request_bytes = request_bytes
                request_bytes = len(built_message)
                built_message[2:4] = struct.pack("H", request_bytes // 4)
                built_message[28:32] = struct.pack("I", new_mask)
                self.queued_bytes = (
                    built_message + self.queued_bytes[orig_request_bytes:]
                )
            if opcode == CHANGE_WINDOW_ATTRIBUTES:
                # Add the override redirect attribute.
                update_mask = struct.unpack("I", self.queued_bytes[8:12])[0]
                logging.debug(
                    f"Change window attributes, update_mask: {update_mask}, and result: {update_mask & OVERRIDE_REDIRECT}"
                )
                if update_mask & OVERRIDE_REDIRECT:
                    logging.debug("Overriding redirect on changed window!")
                    val_i = 0
                    for i in range(32):
                        bit_mask = 1 << i
                        if bit_mask & update_mask:
                            if bit_mask == OVERRIDE_REDIRECT:
                                self.queued_bytes[
                                    12 + 4 * val_i : 12 + 4 * (val_i + 1)
                                ] = struct.pack("I", 1)
                            val_i += 1

            logging.debug(f"Requested opcode: {opcode}, serial: {self.serial}?")
            assert request_bytes > 0, "Reached invalidate state"
            self.request_codes[self.serial] = opcode
            self.serial = (self.serial + 1) % 2**16
            self.send(request_bytes)


class EventReplyParser:
    def __init__(self, socket: socket.socket, request_codes: dict):
        self.message_end = 0
        self.sent_end = 0
        self.messages = []

        # Holds bytes to send and bytes to process. The sent_end will be >= message_end.
        self.byte_buffer = bytearray()
        self.socket = socket
        self.connecting = True
        self.anc_data = []

        self.bytes_to_discard = 0

        self.focused = None
        self.request_codes = request_codes

    # Add the given message to the back of the message queue
    def append_message(self, message):
        self.byte_buffer[self.message_end : self.message_end] = message
        self.message_end += len(message)

    # Commits data from the byte_buffer to the message buffer.
    def commit_message(self, message_len):
        self.messages.append(
            bytearray(
                self.byte_buffer[self.message_end : self.message_end + message_len]
            )
        )
        self.message_end += message_len

    def discard_bytes(self, discard_bytes):
        self.bytes_to_discard += discard_bytes
        remaining = len(self.byte_buffer[self.message_end :])

        if remaining < discard_bytes:
            self.bytes_to_discard -= remaining
            self.byte_buffer = self.byte_buffer[: self.message_end]
        else:
            self.bytes_to_discard = 0
            self.byte_buffer = (
                self.byte_buffer[: self.message_end]
                + self.byte_buffer[self.message_end + 32 :]
            )

    def should_filter_event(self, event_code):
        # if event_code == FOCUS_OUT:
        #     return True
        # return False
        return False

        # Filter FocusOut events.
        if self.focused is None:
            return False

        return (self.focused and event_code == FOCUS_IN) or event_code == FOCUS_OUT

    def consume_anc(self, anc_data):
        self.anc_data = anc_data

    def consume(self, data):
        if self.bytes_to_discard > 0:
            before = len(data)
            data = data[self.bytes_to_discard :]
            after = len(data)
            discarded = before - after
            self.bytes_to_discard -= discarded

        self.byte_buffer += data

        n = len(self.byte_buffer)
        if self.connecting:
            if n < 8:
                return
            logging.debug(
                f"Consuming client received connection setup of {len(self.byte_buffer)} bytes"
            )
            code, major, minor, additional_data_len = struct.unpack(
                "BxHHH", self.byte_buffer[:8]
            )
            assert code == 1, "Client received unexpected connection code " + str(code)
            total_len = 8 + additional_data_len * 4
            if n >= total_len:
                logging.info("Client finished setup")
                self.commit_message(total_len)
                self.connecting = False
            return

        while len(self.byte_buffer) - self.message_end >= 32:
            code, sequence_num, reply_length = struct.unpack(
                "BxHI", self.byte_buffer[self.message_end : self.message_end + 8]
            )
            is_event = code > 1
            is_reply = code == 1
            is_error = code == 0
            if is_reply:
                opcode = self.request_codes.get(sequence_num, -1)
                if opcode == 38:
                    rx, ry, wx, wy = struct.unpack(
                        "HHHH",
                        self.byte_buffer[self.message_end + 16 : self.message_end + 24],
                    )
                    # print("Cursor position:", rx, ry)
                    # Write a new cursor position.
                    self.byte_buffer[
                        self.message_end + 16 : self.message_end + 24
                    ] = struct.pack("HHHH", 1000, 600, 1000, 600)
            if is_event:
                # Unset the send_event bit on all events.
                self.byte_buffer[0] = self.byte_buffer[0] & 0x7F

            # Standard events have code <= 34 and are all 32 bytes.
            # Standard protocol events can sent however we like
            # Extension replies and events are likely safer to send bytes as they
            # arrive.
            #
            # Logic:
            #   If event is filterable && standard:
            #     Remove next 32 bytes
            #   If event is filterable && non-standard:
            #     Throw error, filtering extension events is not implemented
            #   Otherwise continue.
            #
            if is_event:
                additional_length = 0
                # TODO: Should check if FocusIn was already called.
                should_filter = self.should_filter_event(code)

                if code <= LAST_STANDARD_EVENT and should_filter:
                    logging.info(f"Filtering an event. Code {code}")
                    self.discard_bytes(32)
                    continue
                elif code > LAST_STANDARD_EVENT and should_filter:
                    logging.error("UnimplementedError")
                    raise NotImplementedError

                if code == FOCUS_IN:
                    self.focused = True
                elif code == FOCUS_OUT:
                    self.focused = False

                if code == GENERIC_EVENT_CODE:
                    additional_length = struct.unpack(
                        "I",
                        self.byte_buffer[self.message_end + 4 : self.message_end + 8],
                    )[0]

                full_length = 32 + 4 * additional_length
                if n - self.message_end >= full_length:
                    self.commit_message(full_length)
                    continue
            if is_error:
                code = struct.unpack(
                    "xB", self.byte_buffer[self.message_end : self.message_end + 2]
                )
                logging.info(f"X11 Error: {code}")
                self.commit_message(32)
                continue
            if is_reply:
                full_length = 32 + 4 * reply_length
                if n - self.message_end >= full_length:
                    self.commit_message(full_length)
                    continue
                else:
                    break

    def flush(self):
        data = self.byte_buffer[self.sent_end :]
        if len(data) != 0:
            sent = self.socket.sendmsg([data], self.anc_data)
            self.sent_end += sent
            assert sent == len(data)
            logging.debug(f"Wrote: {sent}")

        # Remove all fully processed messages from the byte_buffer.
        self.byte_buffer = self.byte_buffer[self.message_end :]
        self.sent_end -= self.message_end
        self.message_end = 0
        self.messages = []
        self.anc_data = []


def cleanup_anc_data(anc_data):
    for cmsg in anc_data:
        if cmsg[0] != socket.SOL_SOCKET or cmsg[1] != socket.SCM_RIGHTS:
            continue
        fd_bytes = cmsg[2]
        for i in range(0, len(fd_bytes), 4):
            fd = struct.unpack("i", fd_bytes[i : i + 4])[0]
            os.close(fd)


class XServerToClientStream:
    def __init__(self, socket, request_codes: dict):
        self.offset = 0
        self.sequence_number = 0
        self.socket = socket
        self.byte_stream = EventReplyParser(socket, request_codes)

    def sendmsg(self, buffers, anc_data):
        self.socket.sendmsg(buffers, anc_data)
        cleanup_anc_data(anc_data)
        return

        self.byte_stream.consume_anc(anc_data)
        # self.byte_stream.socket.sendmsg([], anc_data)
        for data in buffers:
            self.byte_stream.consume(data)
        for i, message in enumerate(self.byte_stream.messages):
            self.byte_stream.messages[i] = self.process(message)
        self.byte_stream.flush()

        unflushed_len = len(self.byte_stream.byte_buffer)
        if unflushed_len > 0:
            logging.info(
                f"Unflushed: {unflushed_len} on socket: {self.byte_stream.socket}"
            )

    def process(self, message):
        # TODO: Implement filtering.
        return message

    def get_socket(self):
        return self.byte_stream.socket


class XClientToServerStream:
    def __init__(self, socket, request_codes: dict):
        self.socket = socket
        self.connection_bytes = bytes()
        self.parser = RequestParser(socket, request_codes)

    def consume(self, data: bytes):
        self.parser.consume(data)
        if len(self.parser.queued_bytes) > 0:
            logging.info("Queued bytes:", len(self.parser.queued_bytes))

    def sendmsg(self, buffers: Iterable[bytes], anc_data: Iterable[bytes]):
        # TODO: Allow messages with ancillary data to be processed as well.
        # To get this right, we need to send ancillary data at the correct point in the
        # stream. This post describes where in the stream that should be:
        # https://unix.stackexchange.com/questions/185011/what-happens-with-unix-stream-ancillary-data-on-partial-reads
        #
        # For now, we just punt on processing messages that include ancillary data.
        if len(anc_data) > 0:
            logging.debug(
                f"Processing anc_data, data len: {sum([len(b) for b in buffers])}"
            )
            self.socket.sendmsg(buffers, anc_data)
            cleanup_anc_data(anc_data)
            return

        for data in buffers:
            self.consume(data)

    def get_socket(self):
        return self.socket


def _display_path(display_num):
    return "/tmp/.X11-unix/X" + str(display_num)


def parse_display(display_spec: str) -> int:
    split_spec = display_spec.split(":")
    if len(split_spec) == 2:
        host = split_spec[0]
    else:
        host = ""
    display = split_spec[-1]
    assert host == "", "We don't support remote proxies"

    display_split = display.split(".")
    display_num = display_split[0]
    return int(display_num)


class Proxy:
    def __init__(self, client_display_num: int, server_display: str):
        print(f"Hosting proxy on {client_display_num}")
        self.client_display = client_display_num
        server_display_num = parse_display(server_display)
        self.server_display = server_display_num

        self.client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        x_conn_path = _display_path(self.client_display)
        self.client_socket.bind(x_conn_path)
        atexit.register(lambda: os.remove(x_conn_path))
        signal.signal(signal.SIGTERM, lambda signum, frame: os.remove(x_conn_path))
        signal.signal(signal.SIGINT, lambda signum, frame: os.remove(x_conn_path))
        signal.signal(signal.SIGHUP, lambda signum, frame: os.remove(x_conn_path))
        self.client_socket.listen(200)

        self.client_connections: Set[socket.socket] = set()
        self.display_connections: Set[socket.socket] = set()

        self.sockets = [self.client_socket]
        self.mirrors = {}

        self.max_p = 0

    def run(self):
        global first_stream
        while True:
            read, wait, exceptions = select.select(self.sockets, [], self.sockets)
            if len(exceptions) > 0:
                logging.debug("Found %s exception state sockets.", len(exceptions))
            for rs in read:
                if rs is self.client_socket:
                    # Create sockets for the client connection and display connection.
                    logging.info("Client connected")
                    client_connection, address = rs.accept()
                    display_connection = socket.socket(
                        socket.AF_UNIX, socket.SOCK_STREAM
                    )
                    display_connection.setsockopt(
                        socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1
                    )
                    display_connection.connect(_display_path(self.server_display))

                    self.sockets.append(client_connection)
                    self.sockets.append(display_connection)

                    request_codes = {}
                    self.mirrors[client_connection] = XClientToServerStream(
                        display_connection, request_codes
                    )
                    self.mirrors[display_connection] = XServerToClientStream(
                        client_connection, request_codes
                    )
                    if first_stream is None:
                        first_stream = self.mirrors[display_connection]
                    self.client_connections.add(client_connection)
                    self.display_connections.add(display_connection)
                    continue
                else:
                    if rs not in self.sockets:
                        continue

                    mirror_socket = self.mirrors.get(rs, None)
                    if mirror_socket is None:
                        assert False, "No mirror"

                    try:
                        recv_data, anc_data, flags, _ = rs.recvmsg(int(5e5), int(1e4))
                    except ConnectionResetError:
                        logging.info("ConnectionReset cleanup")
                        self.cleanup_from_client(mirror_socket, rs)
                        continue

                    # assert (flags & socket.MSG_TRUNC == 0) and (
                    #     flags & socket.MSG_CTRUNC == 0
                    # )

                    n = len(recv_data)
                    if n > self.max_p:
                        self.max_p = n

                    if len(recv_data) == 0:
                        logging.info("Connection closed cleanup")
                        self.cleanup_from_client(mirror_socket, rs)
                        continue

                    try:
                        mirror_socket.sendmsg([recv_data], anc_data)
                    except BrokenPipeError:
                        logging.info("Client connection broken")
                        self.cleanup_from_server(mirror_socket, rs)
                        continue

    def cleanup_from_client(self, mirror_socket, rs):
        rs.shutdown(socket.SHUT_RDWR)
        mirror_socket.get_socket().shutdown(socket.SHUT_RDWR)
        rs.close()
        mirror_socket.get_socket().close()
        self.sockets.remove(rs)
        self.sockets.remove(mirror_socket.get_socket())
        self.mirrors.pop(rs, None)
        self.mirrors.pop(mirror_socket, None)

    def cleanup_from_server(self, mirror_socket, rs):
        rs.shutdown(socket.SHUT_RDWR)
        mirror_socket.get_socket().shutdown(socket.SHUT_RDWR)
        rs.close()
        mirror_socket.get_socket().close()
        self.sockets.remove(rs)
        self.sockets.remove(mirror_socket.get_socket())
        self.mirrors.pop(rs, None)
        self.mirrors.pop(mirror_socket, None)

    def inject(self, message):
        for client_connection in self.client_connections:
            try:
                client_connection.send(message)
                logging.info("Injected message")
            except BrokenPipeError:
                # print("Failed to inject message")
                pass


if __name__ == "__main__":
    print("Proxy was given argv:", sys.argv, flush=True)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--proxy_display",
        type=int,
        required=True,
        help="The X11 display the proxy will serve traffic for.",
    )
    parser.add_argument(
        "--real_display",
        type=str,
        required=True,
        help="The X11 display the proxy is backed by.",
    )
    args = parser.parse_args()

    print(f"Proxying display: {args.proxy_display} to {args.real_display}", flush=True)
    proxy = Proxy(args.proxy_display, args.real_display)
    proxy.run()
