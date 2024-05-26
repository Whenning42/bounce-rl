import os
import socket
import struct


def cleanup_anc_data(anc_data) -> None:
    for cmsg in anc_data:
        if cmsg[0] != socket.SOL_SOCKET or cmsg[1] != socket.SCM_RIGHTS:
            continue
        fd_bytes = cmsg[2]
        for i in range(0, len(fd_bytes), 4):
            fd = struct.unpack("i", fd_bytes[i : i + 4])[0]
            os.close(fd)
