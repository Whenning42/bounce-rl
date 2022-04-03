# Proxies a new X11 display to an existing one. This is useful for injecting or filtering messages
# between the server and clients. Injecting is not implemented (details of why are in
# serial_numbers.txt). Custom filtering is implemented.
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
#
# TODO: Profile this against ArtOfRally to see if overhead is non-negligible.

import socket
import select
import atexit
import struct
import datetime
import os

# Global first constructed XMessageStream. This is used by main to get the server
# timestamp.
first_stream = None

FOCUS_IN = 9
FOCUS_OUT = 10
LAST_STANDARD_EVENT = 34
GENERIC_EVENT_CODE = 35

def pad(n):
    return n + (4 - (n % 4)) % 4

# Handles stream level operations
class XByteStream():
    def __init__(self, socket):
        self.message_end = 0
        self.sent_end = 0
        self.messages = []

        # Holds bytes to send and bytes to process. The sent_end will be >= message_end.
        self.byte_buffer = bytes()
        self.socket = socket
        self.connecting = True
        self.anc_data = []

        self.bytes_to_discard = 0

        self.focused = None

    # Add the given message to the back of the message queue
    def append_message(self, message):
        self.byte_buffer[self.message_end:self.message_end] = message
        self.message_end += len(message)

    # Commits data from the byte_buffer to the message buffer.
    def commit_message(self, message_len):
        self.messages.append(bytearray(self.byte_buffer[self.message_end : \
                                              self.message_end + message_len]))
        self.message_end += message_len

    def discard_bytes(self, discard_bytes):
        self.bytes_to_discard += discard_bytes
        remaining = len(self.byte_buffer[self.message_end:])

        if remaining < discard_bytes:
            self.bytes_to_discard -= remaining
            self.byte_buffer = self.byte_buffer[:self.message_end]
        else:
            self.bytes_to_discard = 0
            self.byte_buffer = self.byte_buffer[:self.message_end] + self.byte_buffer[self.message_end + 32:]

    def should_filter_event(self, event_code):
        # Filter FocusOut events.
        if self.focused is None:
            return False

        return (self.focused and event_code == FOCUS_IN) \
                             or  event_code == FOCUS_OUT

    def consume_anc(self, anc_data):
        self.anc_data = anc_data

    def consume(self, data):
        # print("Consume")
        if self.bytes_to_discard > 0:
            before = len(data)
            data = data[self.bytes_to_discard:]
            after =  len(data)
            discarded = before - after
            self.bytes_to_discard -= discarded

        self.byte_buffer += data

        l = len(self.byte_buffer)
        if self.connecting:
            if l < 8:
                return
            print("Consuming client received connection setup of", len(self.byte_buffer), "bytes")
            code, major, minor, additional_data_len = struct.unpack('BxHHH', self.byte_buffer[:8])
            assert code == 1, "Client received unexpected connection code " + str(code)
            total_len = 8 + additional_data_len * 4
            if l >= total_len:
                print("Client finished setup")
                self.commit_message(total_len)
                self.connecting = False
            return

        while len(self.byte_buffer) - self.message_end >= 32:
            # print("Buffer len: ", len(self.byte_buffer))
            # print("Read offset: ", self.message_end)
            code, sequence_num, reply_length = struct.unpack('BxHI', self.byte_buffer[self.message_end : self.message_end + 8])
            is_event = code > 1
            is_reply = code == 1
            is_error = code == 0
            if is_reply:
                print("Reply. Sequence num:", sequence_num, "Additional length:", reply_length)
            if is_event:
                print("Event with code:", code)

            # Standard events have code <= 34 and are all 32 bytes.
            # Standard protocol events can sent however we like
            # Extension replies and events are likely safer to send bytes as they arrive.
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
                    print("Filtering an event. Code", code, flush = True)
                    self.discard_bytes(32)
                    continue
                elif code > LAST_STANDARD_EVENT and should_filter:
                    print("UnimplementedError", flush = True)
                    raise NotImplementedError

                if code == FOCUS_IN:
                    self.focused = True
                elif code == FOCUS_OUT:
                    self.focused = False

                if code == GENERIC_EVENT_CODE:
                    additional_length = struct.unpack('I', self.byte_buffer[self.message_end + 4 : self.message_end + 8])[0]

                full_length = 32 + 4 * additional_length
                if l - self.message_end >= full_length:
                    self.commit_message(full_length)
                    continue
            if is_error:
                code = struct.unpack('xB', self.byte_buffer[self.message_end : self.message_end + 2])
                print("Error:", code)
                self.commit_message(32)
                continue
            if is_reply:
                full_length = 32 + 4 * reply_length
                if l - self.message_end >= full_length:
                    self.commit_message(full_length)
                    continue
                else:
                    break

    def flush(self):
        data = self.byte_buffer[self.sent_end : ]
        if len(data) != 0:
            sent = self.socket.sendmsg([data], self.anc_data)
            self.sent_end += sent
            assert sent == len(data)
            print("Wrote: ", sent)

        # Remove all fully processed messages from the byte_buffer.
        self.byte_buffer = self.byte_buffer[self.message_end:]
        self.sent_end -= self.message_end
        self.message_end = 0
        self.messages = []
        self.anc_data = []

class XServerToClientStream:
    def __init__(self, socket):
        self.offset = 0
        self.sequence_number = 0
        self.byte_stream = XByteStream(socket)

    def sendmsg(self, buffers, anc_data):
        self.byte_stream.consume_anc(anc_data)
        # self.byte_stream.socket.sendmsg([], anc_data)
        for data in buffers:
            self.byte_stream.consume(data)
        for i, message in enumerate(self.byte_stream.messages):
            self.byte_stream.messages[i] = self.process(message)
        self.byte_stream.flush()

        unflushed_len = len(self.byte_stream.byte_buffer)
        if unflushed_len > 0:
            print("Unflushed:", unflushed_len, "on socket:", self.byte_stream.socket)

    def process(self, message):
        # TODO: Implement filtering.
        return message

    def close(self):
        self.byte_stream.socket.close()

    def get_socket(self):
        return self.byte_stream.socket

class XClientToServerStream:
    def __init__(self, socket):
        self.socket = socket
        self.is_connected = False
        self.is_little_endian = None
        self.connection_bytes = bytes()

    def consume(self, data):
        self.connection_bytes += data
        if not self.is_connected:
            l = len(self.connection_bytes)
            if l < 12:
                return
            endianess, major, minor, name_len, data_len = struct.unpack('BxHHHH', self.connection_bytes[:10])
            self.is_little_endian = chr(endianess) == 'l'
            assert self.is_little_endian, "XProxy only supports little endian connections"
            self.is_connected = True

    def sendmsg(self, buffers, anc_data):
        self.socket.sendmsg(buffers, anc_data)
        for data in buffers:
            self.consume(data)

    def close(self):
        self.socket.close()

    def get_socket(self):
        return self.socket

def _display_path(display_num):
    return "/tmp/.X11-unix/X" + str(display_num)

class Proxy():
    def __init__(self, client_display_num = 1, server_display_num = 0):
        self.client_display = client_display_num
        self.server_display = server_display_num

        self.client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        x_conn_path = _display_path(self.client_display)
        self.client_socket.bind(x_conn_path)
        atexit.register(lambda: os.remove(x_conn_path))
        self.client_socket.listen(200)

        self.client_connections = set()
        self.display_connections = set()

        self.sockets = [self.client_socket]
        self.mirrors = {}

        self.i = 0
        self.max_p = 0

    def run(self):
        global first_stream
        while True:
            # print("select")
            ### print("desc:", [s.fileno() for s in self.sockets])
            # print("selecting")
            read, _, _ = select.select(self.sockets, [], [])
            # print("read:", [s.fileno() for s in read])
            for rs in read:
                if rs is self.client_socket:
                    # Create sockets for the client connection and display connection.
                    print("Client connected")
                    client_connection, address = rs.accept()
                    display_connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    display_connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    display_connection.connect(_display_path(self.server_display))

                    self.sockets.append(client_connection)
                    self.sockets.append(display_connection)

                    self.mirrors[client_connection] = XClientToServerStream(display_connection)
                    self.mirrors[display_connection] = XServerToClientStream(client_connection)
                    if first_stream is None:
                        first_stream = self.mirrors[display_connection]
                    self.client_connections.add(client_connection)
                    self.display_connections.add(display_connection)
                    break
                else:
                    self.i += 1
                    if self.i % 100000 == 0:
                        print("Proxyied:", self.i)

                    mirror_socket = self.mirrors.get(rs, None)
                    if mirror_socket is None:
                        assert False, "No mirror"

                    recv_data, anc_data, flags, _ = rs.recvmsg(int(5e5), int(1e4))
                    assert (flags & socket.MSG_TRUNC == 0) and (flags & socket.MSG_CTRUNC == 0)

                    l = len(recv_data)
                    if l > self.max_p:
                        ### print("New max payload: ", l)
                        self.max_p = l

                    if len(recv_data) == 0:
                        ### print("Client connection closed")
                        mirror_socket.close()
                        self.sockets.remove(rs)
                        self.sockets.remove(mirror_socket.get_socket())
                        self.mirrors.pop(rs, None)
                        self.mirrors.pop(mirror_socket, None)
                        break

                    try:
                        sent = mirror_socket.sendmsg([recv_data], anc_data)
                        # Our stream wrappers don't implement returning sent bytes.
                        # assert sent == len(recv_data)
                    except BrokenPipeError:
                        print("Client connection broken")

                        # Since mirror_socket.send failed, we know it was closed and is thus the
                        # the client socket.
                        rs.close()
                        self.sockets.remove(rs)
                        self.sockets.remove(mirror_socket.get_socket())
                        self.mirrors.pop(rs, None)
                        self.mirrors.pop(mirror_socket, None)
                        break

    def inject(self, message):
        for client_connection in self.client_connections:
            try:
                client_connection.send(message)
                print("Injected message")
            except BrokenPipeError:
                # print("Failed to inject message")
                pass

import threading
import time
import Xlib.display
import Xlib.X
import struct
from keyboard import Keyboard
if __name__ == "__main__":
    proxy = Proxy()
    t = threading.Thread(target = proxy.run)
    t.start()

    display = Xlib.display.Display()
    window_id = int(input("Enter window id:"), 0)
    window = display.create_resource_object('window', window_id)
    keyboard = Keyboard(display, window)

    t.join()
