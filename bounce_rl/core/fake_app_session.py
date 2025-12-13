"""Test helper for creating fake AppSession instances in unit tests."""

import tempfile


class FakeAppSession:
    """Minimal fake AppSession for testing install_app_from_config.

    Provides just enough interface to test file installation without
    creating real Desktop instances or launching processes.
    """

    def __init__(self, sessions_folder: str):
        """Create a fake session with a temp folder under sessions_folder.

        Args:
            sessions_folder: Parent directory for creating temp session folder
        """
        self._folder = tempfile.TemporaryDirectory(prefix=sessions_folder)

    def data_folder(self) -> str:
        """Return the path to this session's data folder."""
        return self._folder.name

    def cleanup(self):
        """Clean up the temporary folder."""
        if self._folder is not None:
            self._folder.cleanup()
            self._folder = None

    def __del__(self):
        """Ensure cleanup on deletion."""
        if hasattr(self, "_folder") and self._folder is not None:
            self._folder.cleanup()
