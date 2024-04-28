import json
import logging
import time
from socketserver import ThreadingMixIn
from typing import Any
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

import Xlib.display

from bounce_rl.core.launcher import container, x_search

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


class Launcher:
    def _find_windows(
        self,
        window_title: str,
        pid_mapper: container.PIDMapper,
        root_pid: int,
    ) -> list[int]:
        windows: list[Any] = []
        lookup = x_search.WindowLookup(Xlib.display.Display(), pid_mapper, root_pid)
        windows = lookup.get_owned_windows_with_name(window_title)
        return [w.id for w in windows]

    def launch_app(
        self,
        instance: int,
        command: str,
        directory: str,
        env_str: str,  # A json encoded dict[str, str]
        window_title: str,
    ) -> list[int]:
        env = json.loads(env_str)
        # TODO: Catch launch errors.
        unshare_pid, init_pid, pid_mapper = container.launch_process_container(
            command,
            directory,
            env,
        )
        logging.debug("Started unshare subprocess: %s", unshare_pid)
        self.subprocess_pid = unshare_pid
        self.pid_mapper = pid_mapper
        windows = self._find_windows(window_title, pid_mapper, self.subprocess_pid)
        print("Returning", windows)
        return windows

    def kill_instance(self, instance: int) -> None:
        pass
