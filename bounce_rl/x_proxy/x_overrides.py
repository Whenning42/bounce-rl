import logging
import struct
from typing import Callable, Dict, Optional

import Xlib.display
import Xlib.protocol
import Xlib.X
import Xlib.XK
import Xlib.xobject

from bounce_rl.x_proxy import reply_connection, request_connection

# TODO: Consider filtering non-synthetic input events.
# We'd likely need to filter out both core and XI events.

# Event codes
KEY_PRESS = 2
KEY_RELEASE = 3
BUTTON_PRESS = 4
BUTTON_RELEASE = 5
MOTION_NOTIFY = 6
ENTER_NOTIFY = 7
LEAVE_NOTIFY = 8
FOCUS_IN = 9
FOCUS_OUT = 10
GENERIC_EVENT = 35

# Request codes
CREATE_WINDOW = 1
CHANGE_WINDOW_ATTRIBUTES = 2
QUERY_POINTER = 38

# Attribute masks
OVERRIDE_REDIRECT = 0x00000200


def is_send_event(code: int):
    return code & 0x80


def request_handler_table() -> Dict[
    int,
    Callable[
        [
            memoryview,
        ],
        Optional[bytes],
    ],
]:
    return {
        CREATE_WINDOW: handle_create_window_request,
        CHANGE_WINDOW_ATTRIBUTES: handle_change_window_attributes_request,
        QUERY_POINTER: handle_query_pointer_request,
    }


def reply_handler_table() -> Dict[
    int,
    Callable[[memoryview, request_connection.RequestConnection], Optional[bytes]],
]:
    return {QUERY_POINTER: handle_query_pointer_reply}


def event_handler_table() -> (
    Dict[int, Callable[[memoryview, reply_connection.ReplyConnection], Optional[bytes]]]
):
    return {
        MOTION_NOTIFY: handle_motion_notify_event,
        # KEY_PRESS: filter_event,
        # KEY_RELEASE: filter_event,
        # BUTTON_PRESS: filter_event,
        # BUTTON_RELEASE: filter_event,
        # ENTER_NOTIFY: filter_event,
        # LEAVE_NOTIFY: filter_event,
        # FOCUS_IN: filter_event,
        # FOCUS_OUT: filter_event,
        # GENERIC_EVENT: filter_event,
    }


def handle_create_window_request(
    request: memoryview, con: request_connection.RequestConnection, sequence_num: int
) -> Optional[bytes]:
    logging.debug("Overriding redirect on created window!")
    # Add the override redirect attribute.
    orig_mask = struct.unpack("I", request[28:32])[0]
    new_mask = orig_mask | OVERRIDE_REDIRECT
    built_message = bytearray(request[0:32])
    next_val = 0
    for i in range(32):
        bit_mask = 1 << i
        if new_mask & bit_mask:
            if bit_mask != OVERRIDE_REDIRECT:
                built_message += request[32 + 4 * next_val : 32 + 4 * (next_val + 1)]
                next_val += 1
            else:
                # Should this be Bxxx or I? Given that this
                # is little endian, it shouldn't matter.
                built_message += struct.pack("Bxxx", 1)
                if orig_mask & OVERRIDE_REDIRECT:
                    next_val += 1
    request_bytes = len(built_message)
    built_message[2:4] = struct.pack("H", request_bytes // 4)
    built_message[28:32] = struct.pack("I", new_mask)
    return built_message


def handle_change_window_attributes_request(
    request: memoryview, con: request_connection.RequestConnection, sequence_num: int
) -> Optional[bytes]:
    # Add the override redirect attribute.
    update_mask = struct.unpack("I", request[8:12])[0]
    logging.debug(
        f"Change window attributes, update_mask: {update_mask}, "
        f"and result: {update_mask & OVERRIDE_REDIRECT}"
    )
    if update_mask & OVERRIDE_REDIRECT:
        logging.debug("Overriding redirect on changed window!")
        val_i = 0
        for i in range(32):
            bit_mask = 1 << i
            if bit_mask & update_mask:
                if bit_mask == OVERRIDE_REDIRECT:
                    request[12 + 4 * val_i : 12 + 4 * (val_i + 1)] = struct.pack("I", 1)
                val_i += 1


def handle_query_pointer_request(
    request: memoryview, con: request_connection.RequestConnection, sequence_num: int
) -> Optional[bytes]:
    window = struct.unpack("I", request[4:8])[0]
    print("Query pointer window: ", hex(window))


def handle_query_pointer_reply(
    reply: memoryview, con: reply_connection.ReplyConnection
) -> Optional[bytes]:
    con.server_state.lock()
    if con.server_state.pointer_state_init:
        same_screen = reply[1]
        root, child, rx, ry, wx, wy = struct.unpack(
            "IIHHHH",
            reply[8:24],
        )
        # con.server_state.pointer_window = child
        # rx += 1
        # ry += 1
        # wx += 1
        # wy += 1

        # logging.info(
        #     "In Query pointer root: %s, child: %s, new pos: %d, %d, %d, %d",
        #     hex(root),
        #     hex(child),
        #     rx,
        #     ry,
        #     wx,
        #     wy,
        # )
        # tl_x, tl_y = rx - wx, ry - wy
        # logging.info("QP selected win tl  %d, %d", tl_x, tl_y)
        # new_rx, new_ry = (
        #     con.server_state.pointer_root_x,
        #     con.server_state.pointer_root_y,
        # )
        # new_wx, new_wy = new_rx - tl_x, new_ry - tl_y
        # logging.info(
        #     "Out Query pointer root: %s, child: %s, new pos: %d, %d, %d, %d",
        #     hex(root),
        #     hex(con.server_state.pointer_window),
        #     new_rx,
        #     new_ry,
        #     new_wx,
        #     new_wy,
        # )
        # print(
        #     "Writing query pointer reply: ",
        #     hex(con.server_state.pointer_window),
        #     new_rx,
        #     new_ry,
        #     new_wx,
        #     new_wy,
        #     flush=True,
        # )
        # d = Xlib.display.Display()
        # qp_win = d.create_resource_object("window", con.server_state.pointer_window)
        # print("QP Reply window Geom: ", qp_win.get_geometry(), flush=True)
        print("QP same-screen? ", same_screen, flush=True)
        reply[12:24] = struct.pack("Ihhhh", child, rx, ry, wx, wy)
    con.server_state.unlock()
    return None


def handle_motion_notify_event(
    event: memoryview, con: reply_connection.ReplyConnection
) -> Optional[bytes]:
    (
        code,
        detail,
        sequence_num,
        time,
        root_win,
        event_win,
        child_win,
        rx,
        ry,
        wx,
        wy,
        mask,
        same_screen,
    ) = struct.unpack("BBHIIIIhhhhHBx", event[0:32])
    logging.info("Motion notify handler with code: %d", code)

    if is_send_event(code):
        logging.info(
            "Handling send event motion notify. New pointer pos: %d, %d, New ptr win: %s",
            rx,
            ry,
            hex(event_win),
        )
        con.server_state.lock()
        con.server_state.pointer_state_init = True
        con.server_state.pointer_window = event_win
        con.server_state.pointer_root_x = rx
        con.server_state.pointer_root_y = ry
        con.server_state.unlock()

        d = Xlib.display.Display()
        event_win = d.create_resource_object("window", event_win)
        print("Geom: ", event_win.get_geometry(), flush=True)

        return None
    else:
        return memoryview(b"")


def filter_event(
    event: memoryview, con: reply_connection.ReplyConnection
) -> Optional[bytes]:
    code = struct.unpack("B", event[0:1])[0]
    logging.info("Filtering event with code: %d", code)
    return memoryview(b"")
