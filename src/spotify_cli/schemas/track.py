from pydantic import BaseModel

from spotify_cli.schemas.search import AlbumSearchItem


class Track(BaseModel):
    name: str
    artist: str
    album: AlbumSearchItem
    is_playing: bool

# class TrackAlbum(BaseModel):
#     name: str
#     image_url: str