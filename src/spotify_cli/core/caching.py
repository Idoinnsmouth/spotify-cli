import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic

from platformdirs import user_cache_dir
from pydantic import BaseModel

from spotify_cli.schemas.search import AlbumSearchItem

T = TypeVar("T")


class JsonCacheBase(ABC, Generic[T]):
    schema_version: int = 1

    def __init__(self, path: Path):
        self.path = path

    @abstractmethod
    def default_payload(self) -> T:
        ...

    @abstractmethod
    def from_json(self, data: dict) -> T:
        ...

    @abstractmethod
    def to_json(self, payload: T) -> dict:
        ...

    @abstractmethod
    def migrate(self, data: dict) -> dict:
        """Upgrade data from older data"""
        ...

    def load(self) -> T | None:
        if not self.path.exists():
            return None
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            # catch corrupted files
            return None

        if "schema_version" not in data:
            data["schema_version"] = 0

        if data["schema_version"] != self.schema_version:
            data = self.migrate(data)
            data["schema_version"] = self.schema_version

        return self.from_json(data)

    def save(self, payload: T):
        data = self.to_json(payload)
        data["schema_version"] = self.schema_version

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=self.path.parent, delete=False, encoding="utf-8") as temp:
            json.dump(data, temp, ensure_ascii=False)
            temp.flush()
            os.fsync(temp.fileno())
            temp_name = temp.name
        os.replace(temp_name, self.path)

    def invalidate(self):
        try:
            if self.path.exists():
                self.path.unlink()
        except OSError:
            pass


class SavedAlbumsModel(BaseModel):
    latest_added_at: str | None = None
    entries: list['EntryModel'] = []
    album_ids: list[str] = []
    updated_ts: float = 0.0


class EntryModel(BaseModel):
    album: AlbumSearchItem
    added_at: str


class SavedAlbumsCache(JsonCacheBase[SavedAlbumsModel]):
    schema_version = 1

    def default_payload(self) -> SavedAlbumsModel:
        return SavedAlbumsModel()

    def from_json(self, data: dict) -> SavedAlbumsModel:
        return SavedAlbumsModel.model_validate(data)

    def to_json(self, payload: SavedAlbumsModel) -> dict:
        return payload.model_dump()

    def migrate(self, data: dict) -> dict:
        v = data.get("schema_version", 0)

        if v < 1:
            data.setdefault("latest_added_at", None)
            data.setdefault("entries", [])
            data.setdefault("album_ids", [])
            data.setdefault("updated_ts", 0.0)

        return data


def get_saved_albums_cache_path() -> Path:
    return Path(user_cache_dir("spotify-cli")) / "saved_albums.json"


class SpotipyTokenModel(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    expires_at: int
    refresh_token: str


def get_spotipy_cache_path():
    return Path(user_cache_dir("spotify-cli")) / "spotipy_token.json"
