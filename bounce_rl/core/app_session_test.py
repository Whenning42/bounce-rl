import os
import subprocess
import tempfile
import unittest

import bounce_desktop
import libtimecontrol
from app_session import AppSession


class TestAppSession(unittest.TestCase):
    def setUp(self):
        self._sessions_dir = tempfile.TemporaryDirectory()
        self.sessions_dir = self._sessions_dir.name

    def assertDictContainsSubset(self, subset, dictionary):
        return self.assertLessEqual(subset.items(), dictionary.items())

    def tearDown(self):
        self._sessions_dir.cleanup()

    def test_temp_folder(self):
        s = AppSession(self.sessions_dir, "")
        self.assertIsInstance(s._folder, tempfile.TemporaryDirectory)
        self.assertTrue(os.path.exists(s.data_folder()))

    def test_start_process_launches_subprocess(self):
        # "whoami" is a simple binary that should be present across platforms.
        s = AppSession(self.sessions_dir, ["whoami"])
        s.start_process()
        self.assertIsInstance(s._process, subprocess.Popen)

    def test_time_controller(self):
        s = AppSession(self.sessions_dir, "")
        self.assertIsInstance(s.time_controller(), libtimecontrol.TimeController)

    def test_time_control_env_passed_to_subprocess(self):
        p_args = []
        p_kwargs = {}

        def test_popen(*args, **kwargs):
            nonlocal p_args, p_kwargs
            p_args = args
            p_kwargs = kwargs

        s = AppSession(self.sessions_dir, ["whoami"])
        s._popen = test_popen
        s.start_process()
        self.assertEqual(p_args[0], ["whoami"])
        self.assertDictContainsSubset(
            s.time_controller().child_flags(), p_kwargs.get("env")
        )

    # TODO: Implement desktop launching.
    # def test_desktop(self):
    #     s = AppSession(self.sessions_dir, "")
    #     self.assertIsInstance(s.desktop(), bounce_desktop.Desktop)


if __name__ == "__main__":
    unittest.main()
