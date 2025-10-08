import json
from copy import deepcopy
from pathlib import Path
from typing import TypedDict

from spotify_cli.schemas.search import AlbumSearchItem

CACHE_DIR = Path.home() / ".spotify_cli_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# todo - refactor this to be used in caching aso the spotify and env stuff
class SavedAlbumsCache(TypedDict):
    latest_added_at: str | None
    entries: list['EntryCache']
    album_ids: list[str]
    updated_ts: float


class EntryCache(TypedDict):
    album: AlbumSearchItem
    last_added_at: str


def cache_path() -> Path:
    return CACHE_DIR / f"saved_albums.json"


def load_cache(path: Path) -> SavedAlbumsCache | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # ensure keys exist (forward-compatible)
    data.setdefault("latest_added_at", None)
    data.setdefault("entries", [])
    data.setdefault("album_ids", [])
    data.setdefault("updated_ts", 0.0)

    data["entries"] = [AlbumSearchItem(**entry["album"]) for entry in data["entries"]]
    # data["entries"] = [AlbumSearchItem(**entry) for entry in data["entries"]]
    return data


def save_cache(path: Path, cache: SavedAlbumsCache) -> None:
    with path.open("w", encoding="utf-8") as f:
        _cache = deepcopy(cache)
        _cache["entries"] = [
            {
                "album": entry["album"].model_dump(),
                "added_at": entry["added_at"],
            } for entry in _cache["entries"]
        ]

        json.dump(_cache, f, ensure_ascii=False)


def new_cache() -> SavedAlbumsCache:
    return {
        "latest_added_at": None,
        "entries": [],
        "album_ids": [],
        "updated_ts": 0.0,
    }


def invalidate_saved_albums_cache() -> None:
    """Clear the per-user saved albums cache."""
    path = cache_path()
    try:
        if path.exists():
            path.unlink()
    except OSError:
        # it's okay if we fail to delete; we'll overwrite on next save
        pass
