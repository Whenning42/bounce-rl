import tempfile
import unittest
from pathlib import Path

import gymnasium as gym
import numpy as np
import yaml

from bounce_rl.core.app_environment import (
    AppEnvironment,
    install_app_from_config,
    load_app_config,
)
from bounce_rl.core.fake_app import FakeApp, fake_app_config
from bounce_rl.core.fake_app_session import FakeAppSession
from bounce_rl.input import gym_input


class TestLoadAppConfig(unittest.TestCase):
    def test_load_app_config_loads_global_config(self):
        """Verify load_app_config loads a non-empty config."""
        config = load_app_config("Factorio")
        self.assertIsInstance(config, dict)
        self.assertGreater(len(config), 0)

    def test_load_app_config_loads_app_data(self):
        app_conf = {"name": "my_app", "entrypoint": "my_entrypoint"}
        conf = {"apps": [app_conf]}
        with tempfile.NamedTemporaryFile(mode="w") as f:
            yaml.dump(conf, f)
            read_app_conf = load_app_config("my_app", f.name)
            self.assertEqual(read_app_conf, app_conf)


class TestInstallAppFromConfig(unittest.TestCase):
    def test_install_app_from_config(self):
        """Verify install_app_from_config copies files and directories correctly."""
        with tempfile.TemporaryDirectory() as _temp_dir, tempfile.TemporaryDirectory() as _sessions_dir:
            temp_dir = Path(_temp_dir)
            src_file = temp_dir / "test_file.txt"
            src_file.write_text("test content")

            session = FakeAppSession(_sessions_dir)
            config = {
                "install": [
                    {"from": str(src_file), "to": "dest_file.txt"},
                    {"from": str(temp_dir), "to": "dest_dir"},
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
        with tempfile.TemporaryDirectory() as sessions_dir:
            session = FakeAppSession(sessions_dir)
            config = {"name": "TestApp"}
            install_app_from_config(session, config)


class TestAppEnvironment(unittest.TestCase):
    def test_action_space(self):
        with tempfile.NamedTemporaryFile(mode="w") as f:
            yaml.dump(fake_app_config(), f)
            env = AppEnvironment(
                FakeApp, (640, 480), session_cls=FakeAppSession, config_path=f.name
            )
            self.assertEqual(env.action_space, gym_input.action_space(640, 480))

    def test_observation_space(self):
        with tempfile.NamedTemporaryFile(mode="w") as f:
            yaml.dump(fake_app_config(), f)
            env = AppEnvironment(
                FakeApp, (640, 480), session_cls=FakeAppSession, config_path=f.name
            )
            self.assertEqual(
                env.observation_space, gym.spaces.Box(0, 255, (3, 640, 480), np.uint8)
            )


if __name__ == "__main__":
    unittest.main()
