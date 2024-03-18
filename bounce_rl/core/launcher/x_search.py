# TODO: Move from ownership tracking via pid tree to ownership via xresource API.
# We can get the app root PID from unshare and then use the descendant PID tree along
# w/ the X resources API to filter candidate windows to those that are owned by the
# launched app.

import logging
import re
import time

import psutil
import Xlib
from Xlib.display import Display
from Xlib.xobject.drawable import Window

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


def query_window_property(
    display: Display,
    window: Window,
    property_name: str,
    property_type,
) -> list[int]:
    property_name_atom = display.get_atom(property_name)
    try:
        result = window.get_full_property(property_name_atom, property_type)
        if result:
            return list(result.value)
        else:
            return []
    except Xlib.error.BadWindow:
        return [-1]


def get_all_windows_with_name(name: str, parent: Window, matches: list) -> list:
    try:
        for child in parent.query_tree().children:
            wm_name = child.get_wm_name()
            if wm_name is not None:
                if isinstance(wm_name, bytes):
                    wm_name = wm_name.decode("utf-8")
            if wm_name is not None and re.match(name, wm_name):
                matches.append(child)
            matches = get_all_windows_with_name(name, child, matches)
        return matches
    except:
        return matches


class WindowLookup:
    def __init__(self, display, pid_mapper, root_pid):
        self.display = display
        self.pid_mapper = pid_mapper
        self.root_pid = root_pid

    # Return True if the window's process is a descendant of any of the child_pids.
    def _is_owned(self, window: Window):
        # Note: Requires the application to set _NET_WM_PID annotations on the window.
        window_pid_result = query_window_property(
            self.display, window, "_NET_WM_PID", Xlib.Xatom.CARDINAL
        )
        assert (
            window_pid_result is not None
        ), "Harness requires the running window manager to implement _NET_WM_PID annotations."
        window_pid = window_pid_result[0]
        logging.debug("Got window pid: %s", window_pid)
        # The _NET_WM_PID will be a pid in the container namespace. We need to map it
        # back to the host pid namespace.
        host_pid = self.pid_mapper.get(window_pid)
        window_ps = psutil.Process(host_pid)

        is_owned = False
        ancestor = window_ps
        while ancestor is not None:
            if ancestor.pid == self.root_pid:
                is_owned = True
                break
            ancestor = ancestor.parent()

        # logging.debug(
        #     "Is owned query: window: %s, window_pid: %s, mapped_pid: %s, is_owned: %s",
        #     window.id,
        #     window_pid,
        #     host_pid,
        #     is_owned,
        # )
        return is_owned

    def get_owned_windows_with_name(self, name: str) -> list[Window]:
        windows: list[Window] = []
        while len(windows) == 0:
            time.sleep(0.5)
            logging.debug("Looking for windows with name: %s", name)
            all_windows = get_all_windows_with_name(
                name, self.display.screen().root, []
            )
            windows = [w for w in all_windows if self._is_owned(w)]
        logging.debug("Found windows!")
        return windows
