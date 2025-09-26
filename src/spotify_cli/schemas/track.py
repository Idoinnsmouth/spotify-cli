from typing import Optional

from pydantic import BaseModel

from spotify_cli.schemas.device import Device
from spotify_cli.schemas.search import AlbumSearchItem


class Track(BaseModel):
    name: str
    artist: str
    album: AlbumSearchItem
    device: Device
    actions: Optional['Actions'] = None
    is_playing: bool


class Actions(BaseModel):
    disallows: 'Disallows'


class Disallows(BaseModel):
    pausing: bool | None = None
    resuming: bool | None = None

# class TrackAlbum(BaseModel):
#     name: str
#     image_url: str
