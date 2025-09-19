import os
from dataclasses import dataclass

from dotenv import load_dotenv

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class Config(metaclass=Singleton):
    client_id: str
    client_secret: str
    redirect_uri: str
    cache_path: str
    scopes: str

    def __init__(self):
        self._load_config()

    def _load_config(self):
        # Load .env from project root or user config dir
        parent_dir = os.path.dirname(os.path.realpath(__file__))
        cwd_env = os.path.join(parent_dir, "..", "..", ".env")
        load_dotenv(cwd_env)

        self.client_id=os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8080/callback")
        self.cache_path = os.path.join(parent_dir,"..", "..", ".cache")
        self.scopes = "user-modify-playback-state user-read-playback-state app-remote-control streaming"