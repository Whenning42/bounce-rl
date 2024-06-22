import argparse
import atexit
import logging
import os
import select
import signal
import socket
import sys

from bounce_rl.x_proxy import reply_connection, request_connection, server_state

logging.basicConfig(level=logging.INFO)


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

        self.sockets = [self.client_socket]
        self.conn_id = 0
        self.proxy_connections = {}
        self.server_state = server_state.ServerState()

    def run(self):
        while True:
            read, wait, exceptions = select.select(self.sockets, [], self.sockets)
            if len(exceptions) > 0:
                logging.debug("Found %s exception state sockets.", len(exceptions))
            for rs in read:
                if rs is self.client_socket:
                    # Create sockets for the client connection and display connection.
                    logging.info("Client connected")
                    client_sock, address = rs.accept()
                    display_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    display_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    display_sock.connect(_display_path(self.server_display))

                    self.sockets.append(client_sock)
                    self.sockets.append(display_sock)

                    requests = request_connection.RequestConnection(
                        display_sock, self.conn_id, self.server_state
                    )
                    replies = reply_connection.ReplyConnection(
                        client_sock,
                        requests.request_stream.request_codes,
                        self.conn_id,
                        self.server_state,
                    )
                    self.conn_id += 1
                    self.proxy_connections[client_sock] = requests
                    self.proxy_connections[display_sock] = replies
                    continue
                else:
                    if rs not in self.sockets:
                        continue

                    mirror_socket = self.proxy_connections.get(rs, None)
                    if mirror_socket is None:
                        assert False, "No mirror"

                    try:
                        recv_data, anc_data, flags, _ = rs.recvmsg(int(5e5), int(1e4))
                    except ConnectionResetError:
                        logging.info("ConnectionReset cleanup")
                        self.cleanup_from_client(mirror_socket, rs)
                        continue

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
        self.proxy_connections.pop(rs, None)
        self.proxy_connections.pop(mirror_socket, None)

    def cleanup_from_server(self, mirror_socket, rs):
        rs.shutdown(socket.SHUT_RDWR)
        mirror_socket.get_socket().shutdown(socket.SHUT_RDWR)
        rs.close()
        mirror_socket.get_socket().close()
        self.sockets.remove(rs)
        self.sockets.remove(mirror_socket.get_socket())
        self.proxy_connections.pop(rs, None)
        self.proxy_connections.pop(mirror_socket, None)


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
