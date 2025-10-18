import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigValuesError(Exception):
    pass


@dataclass
class Config(metaclass=Singleton):
    client_id: str = None
    client_secret: str = None
    redirect_uri: str = "http://127.0.0.1:8080/callback"
    scopes: str = "user-modify-playback-state user-read-playback-state app-remote-control streaming user-library-read"

    def load_config(self):
        load_dotenv(get_env_path())

        self.client_id = os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        if self.client_id is None or self.client_secret is None:
            raise ConfigValuesError()


def save_config(client_id: str, client_secret: str):
    with open(get_env_path(), "w") as f:
        f.write(f"""SPOTIPY_CLIENT_ID={client_id}\nSPOTIPY_CLIENT_SECRET={client_secret}""")


def get_env_path() -> Path:
    if os.name == "nt":  # Windows
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:  # macOS/Linux
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = base / "spotify_cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / ".env"
