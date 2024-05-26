import logging
import struct
from typing import Callable, Dict, Optional

# Request codes
CREATE_WINDOW = 1
CHANGE_WINDOW_ATTRIBUTES = 2
QUERY_POINTER = 38

# Attribute masks
OVERRIDE_REDIRECT = 0x00000200


def RequestHandlerTable() -> Dict[int, Callable[[memoryview], Optional[bytes]]]:
    return {
        CREATE_WINDOW: HandleCreateWindowRequest,
        CHANGE_WINDOW_ATTRIBUTES: HandleChangeWindowAttributesRequest,
        QUERY_POINTER: HandleQueryPointerRequest,
    }


def ReplyHandlerTable() -> Dict[int, Callable[[memoryview], Optional[bytes]]]:
    return {QUERY_POINTER: HandleQueryPointerReply}


def EventHandlerTable() -> Dict[int, Callable[[memoryview], Optional[bytes]]]:
    return {}


def HandleQueryPointerReply(reply: memoryview) -> Optional[bytes]:
    root, child, rx, ry, wx, wy = struct.unpack(
        "IIHHHH",
        reply[8:24],
    )
    print("Query pointer real pos:", hex(root), hex(child), rx, ry, wx, wy)
    # Write a new cursor position.
    tl, tr = rx - wx, ry - wy
    x, y = 500, 200
    nrx = tl + x
    nry = tr + y
    nwx = tl + x
    nwy = tr + y
    print("Query pointer fake pos:", nrx, nry, nwx, nwy)
    reply[16:24] = struct.pack("HHHH", nrx, nry, nwx, nwy)
    return None


def HandleCreateWindowRequest(request: memoryview) -> Optional[bytes]:
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


def HandleChangeWindowAttributesRequest(request: memoryview) -> Optional[bytes]:
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


def HandleQueryPointerRequest(request: memoryview) -> Optional[bytes]:
    window = struct.unpack("I", request[4:8])[0]
    print("Query pointer window: ", hex(window))
