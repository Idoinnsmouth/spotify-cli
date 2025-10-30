import os
from pathlib import Path

import pytest

from spotify_cli.core import config
from spotify_cli.core.config import ConfigValuesError, Config, save_config


test_file = Path(Path(__file__).parent.resolve() / ".test_config")

@pytest.fixture(scope="class")
def clean_up_files():
    yield
    os.remove(test_file)

class TestConfig:
    def test_load_config_returns_error_if_not_client_id_or_client_secret(self, monkeypatch):
        monkeypatch.setattr(
            os,
            "getenv",
            lambda _: None,
        )

        monkeypatch.setattr(
            config,
            "get_env_path",
            lambda: None,
        )

        with pytest.raises(ConfigValuesError):
            Config()

    def test_save_config(self, monkeypatch, clean_up_files):
        monkeypatch.setattr(
            config,
            "get_env_path",
            lambda: test_file,
        )

        save_config(
            client_id="test",
            client_secret="test-secret"
        )

        with open(test_file, "r") as f:
            assert f.read() == "SPOTIPY_CLIENT_ID=test\nSPOTIPY_CLIENT_SECRET=test-secret"