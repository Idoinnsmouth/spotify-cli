from typing import Literal, Union, Optional

from pydantic import BaseModel, Field

from spotify_cli.schemas.images import SpotifyImage


class SearchResult(BaseModel):
    href: str
    limit: int
    next: str
    offset: int
    previous: str | None
    total: int
    items: list['ArtistSearchItem'] | list['AlbumSearchItem'] | list['TracksSearchItems']

    def get_item_by_index(self, idx=0) -> Union['ArtistSearchItem', 'AlbumSearchItem', 'TracksSearchItems']:
        return self.items[idx]

class ArtistSearchItem(BaseModel):
    genres: Optional[list[str]] = None
    href: str
    id: str
    name: str
    popularity: Optional[int] = Field(ge=0, le=100, default=None)
    type: str
    uri: str


class AlbumSearchItem(BaseModel):
    album_type: Literal["album", "single", "compilation"]
    total_tracks: int
    available_markets: list[str]
    href: str
    id: str
    images: list[SpotifyImage]
    name: str
    release_date: str
    type: str
    uri: str
    artists: list[ArtistSearchItem]


class TracksSearchItems(BaseModel):
    album: Optional[AlbumSearchItem] = None
    artists: list[ArtistSearchItem]
    available_markets: Optional[list[str]] = None
    duration_ms: int
    href: str
    id: str
    is_playable: bool
    popularity: Optional[int] = Field(ge=0, le=100, default=None)
    track_number: int
    type: str
    uri: str
    name: str


