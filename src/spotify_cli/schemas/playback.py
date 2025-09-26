from typing import Optional

from pydantic import BaseModel
from textual.message import Message

from spotify_cli.schemas.device import Device
from spotify_cli.schemas.search import AlbumSearchItem
from spotify_cli.schemas.track import Track


class PlaybackState(BaseModel):
    track: Optional[Track]
    progress_ms: Optional[int]
    duration_ms: Optional[int]
    is_playing: bool
    device_id: Optional[str]
    etag: Optional[str] = None


    @staticmethod
    def to_state(payload: dict | None) -> Optional['PlaybackState']:
        if not payload:
            return None
        item = payload.get("item", {})
        album = item.get("album")
        return PlaybackState(
            track=Track(
                name=item.get("name"),
                artist=item.get("artists")[0]["name"],
                album=AlbumSearchItem(**album),
                device=Device(**payload.get("device")),
                is_playing=payload.get("is_playing", False),
            ),
            progress_ms=payload.get("progress_ms"),
            duration_ms=item.get("duration_ms"),
            is_playing=payload.get("is_playing", False),
            device_id=payload.get("device").get("id")
        )
