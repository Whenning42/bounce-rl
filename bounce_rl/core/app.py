# Instances of the App class implement app-specific BounceRL integrations.

from typing import Any, Protocol

# TODO: Use real types instead of placeholders
Info = Any
ActionType = Any
AppSession = Any


class App(Protocol):
    def step() -> tuple[float, bool, bool, Info]:
        """Returns (reward, terminated, truncated, info)"""
        pass

    def input_map() -> dict[str, ActionType]:
        """A mapping from input axis names to action types"""
        pass

    def start() -> AppSession:
        """Launch the app and run any macros to get it to its environment initial state.

        Returns an AppSession holding the platform specific app state incl.
        - Session folders
        - Virtual desktop handles
        - Time controller
        - Root process"""
        pass

    def supports_resolution(width: int, height: int) -> bool:
        """Returns True if the given resolution is supported by this app."""
        pass

    # TODO:
    # d Figure out return type of input_map()
    # - Figure out interface for declaring supported app resolutions
