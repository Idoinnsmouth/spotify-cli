from pydantic import BaseModel


class Track(BaseModel):
    name: str
    artist: str
    album: str
    is_playing: bool