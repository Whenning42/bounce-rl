import atexit
import os
from pathlib import Path
from typing import Optional


# Note: We can consider other for message passing the from mod to this file.
# Options include:
#  - Files
#  - Named pipes
#  - Shared memory
#  - Sockets
class FileTail:
    def __init__(self, path: str, mode: str = "r", initial_line: Optional[str] = None):
        self.path = path
        self.file = open(path, mode)
        self.position = 0
        self.partial_line = ""
        if initial_line is None:
            initial_line = ""
        self.line = initial_line

    def get(self) -> tuple[str, bool]:
        """Returns the most recently seen line and whether a new line has been read."""
        is_new = False
        while True:
            self.file.seek(self.position)
            line = self.file.readline()
            if line and line.endswith("\n"):
                is_new = True
                self.position = self.file.tell()
                self.line = line
            else:
                return self.line, is_new


class NoitaInfo:
    def __init__(self, pipe_dir: str = "/tmp/rl_env"):
        self.is_alive = False
        Path(pipe_dir).mkdir(parents=True, exist_ok=True)

        # Keep in sync with noita noita mod init.lua.
        self.info = {
            "biome": "",
            "hp": 100,
            "max_hp": 100,
            "gold": 0,
            "x": 0,
            "y": 0,
            "tick": 0,
            "polymorphed": 0,
        }
        self.info_file = os.path.join(pipe_dir, "noita_stats.tsv")
        self.info_tail = FileTail(
            self.info_file, "a+", ", ".join([str(v) for v in self.info.values()])
        )

        self.notification_file = os.path.join(pipe_dir, "noita_notifications.txt")
        self.notification_tail = FileTail(self.notification_file, "a+")

        atexit.register(self.cleanup)

        # Clear any existing notifications.
        self.on_tick()
        self.is_alive = True

    def current_info(self) -> dict:
        return self.info.copy()

    def on_tick(self) -> dict:
        # Update info
        new_vals_line, new_data = self.info_tail.get()
        self.is_alive = new_data or self.is_alive
        new_vals = new_vals_line.split("\t")
        for k, v in zip(self.info.keys(), new_vals):
            if k != "biome":
                v = int(v)
            self.info[k] = v

        # Update is_alive
        line, did_die = self.notification_tail.get()
        if did_die:
            print("Found death notification")
            self.is_alive = False

        self.info["is_alive"] = self.is_alive
        return self.info.copy()

    def cleanup(self) -> None:
        if self.info_tail is not None:
            self.info_tail.file.close()
            self.info_tail = None
        if self.notification_tail is not None:
            self.notification_tail.file.close()
            self.notification_tail = None
