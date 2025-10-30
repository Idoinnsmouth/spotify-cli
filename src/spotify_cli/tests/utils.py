import uuid

from spotify_cli.schemas.device import Device
from spotify_cli.schemas.images import SpotifyImage
from spotify_cli.schemas.playback import PlaybackState
from spotify_cli.schemas.search import AlbumSearchItem, ArtistSearchItem
from spotify_cli.schemas.track import Track, Actions, Disallows


def generate_test_track_instance() -> Track:
    track = Track(
        name="test name",
        artist="test artist",
        album=generate_test_album_search_item(),
        device=generate_test_device(),
        actions=None,
        is_playing=False
    )

    return track


def generate_test_album_search_item(
        name: str = "test album",
) -> AlbumSearchItem:
    album_search_item = AlbumSearchItem(
        album_type="album",
        total_tracks=10,
        available_markets=["eu"],
        href="https://....",
        id=str(uuid.uuid4()),
        images=[],
        name=name,
        release_date="2025-01-01",
        type="album",
        uri=f"spotify:album:{str(uuid.uuid4())}",
        artists=[generate_artist_search_item()]
    )

    return album_search_item


def generate_artist_search_item() -> ArtistSearchItem:
    artist_search_item = ArtistSearchItem(
        genres=["rock"],
        href="https://...",
        name="test artist",
        popularity=None,
        type="artist",
        uri="spotify:artist:0EANQDy9R0iyVz27nGiDvQ",
        id="artist123"
    )

    return artist_search_item


def generate_test_device(name: str = "device", is_active: bool = False) -> Device:
    device = Device(
        id=f"device{uuid.uuid4()}",
        is_active=is_active,
        is_private_session=True,
        is_restricted=False,
        name=name,
        type="device",
        volume_percent=100,
        supports_volume=True,
    )
    return device


def generate_test_playback_state(is_playing: bool = True, device_id: str = None, is_pausable: bool = True,
                                 is_resumable: bool = True) -> PlaybackState:
    return PlaybackState(
        track=generate_test_track_instance(),
        progress_ms=0,
        duration_ms=200,
        is_playing=is_playing,
        device_id=device_id,
        actions=Actions(
            disallows=Disallows(
                pausing=(not is_pausable),
                resuming=(not is_resumable)
            )
        ),
        etag=None
    )


class MockSpotify:
    def __init__(
            self,
            auth=None,
            requests_session=True,
            client_credentials_manager=None,
            oauth_manager=None,
            auth_manager=None,
            proxies=None,
            requests_timeout=5,
            status_forcelist=None,
            retries=5,
            status_retries=5,
            backoff_factor=0.3,
            language=None,
    ):
        pass


class MockPlatformAdapter:
    def __init__(self):
        pass
