from pydantic import BaseModel


class SpotifyImage(BaseModel):
    url: str
    height: int
    width: int