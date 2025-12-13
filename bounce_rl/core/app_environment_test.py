import tempfile
import unittest
from pathlib import Path

import yaml

from bounce_rl.core.app_environment import install_app_from_config, load_app_config
from bounce_rl.core.fake_app_session import FakeAppSession


class TestLoadAppConfig(unittest.TestCase):
    def test_load_app_config_loads_global_config(self):
        """Verify load_app_config loads a non-empty config."""
        config = load_app_config("Factorio")
        self.assertIsInstance(config, dict)
        self.assertGreater(len(config), 0)

    def test_load_app_config_loads_app_data(self):
        app_conf = {"name": "my_app", "entrypoint": "my_entrypoint"}
        conf = {"apps": [app_conf]}
        with tempfile.NamedTemporaryFile() as f:
            yaml.dump(conf, f)
            read_app_conf = load_app_config("my_app", f.name)
            self.assertEqual(read_app_conf, app_conf)


class TestInstallAppFromConfig(unittest.TestCase):
    def test_install_app_from_config(self):
        """Verify install_app_from_config copies files and directories correctly."""
        with tempfile.NamedTemporaryDirectory() as _temp_dir, tempfile.NamedTemporaryDirectory() as _sessions_dir:
            temp_dir = Path(_temp_dir.name)
            src_file = temp_dir / "test_file.txt"
            src_file.write_text("test content")

            session = FakeAppSession(_sessions_dir.name)
            config = {
                "install": [
                    {"from": str(self.src_file), "to": "dest_file.txt"},
                    {"from": str(self.temp_dir), "to": "dest_dir"},
                ]
            }
            install_app_from_config(session, config)

            dest_file = Path(session.data_folder()) / "dest_file.txt"
            dest_dir_file = Path(session.data_folder()) / "dest_dir" / "test_file.txt"
            self.assertTrue(dest_file.exists())
            self.assertTrue(dest_dir_file.exists())

    def test_install_app_from_config_handles_missing_install_key(self):
        """Verify install_app_from_config doesn't throw an exception when no install is
        given."""
        session = FakeAppSession(self.sessions_dir)
        config = {"name": "TestApp"}
        install_app_from_config(session, config)


if __name__ == "__main__":
    unittest.main()
