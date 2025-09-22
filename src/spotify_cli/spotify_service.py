import subprocess
import time
from enum import Enum

from spotipy import Spotify

from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.schemas.device import Device
from spotify_cli.schemas.search import SearchResult, AlbumSearchItem, TracksSearchItems
from spotify_cli.schemas.track import Track


class SearchElementTypes(Enum):
    ARTIST="artist"
    ALBUM="album"
    TRACK="track"


class NoArtistFound(Exception):
    def __str__(self):
        return "No artist found"

class NoAlbumsFound(Exception):
    def __str__(self):
        return "No albums found"

class NoTrackFound(Exception):
    def __str__(self):
        return "No track found"

class NoActiveDeviceFound(Exception):
    def __str__(self):
        return "No active device found"

#region #### Check Spotify client ####

def ensure_spotify_running():
    # todo - this runs spotify on current machine only
    try:
        subprocess.run(["pgrep", "-x", "Spotify"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.run(["open", "-a", "Spotify"])
        time.sleep(1.5)


def get_devices(sp: Spotify) -> list[Device]:
    resp = sp.devices()
    return [Device(**device) for device in resp.get("devices", [])]

def get_first_active_device(sp) -> Device:
    devices = get_devices(sp=sp)
    return next((_device for _device in devices if _device.is_active), devices[0])

# todo - turn this to async func
def wait_for_device(sp, tries=12, delay=0.5) -> Device | None:
    for _ in range(tries):
        active_device = get_first_active_device(sp)
        if active_device:
            return active_device
        time.sleep(delay)
    return None
#endregion

#region #### Playback ####
def search_spotify(sp: Spotify, query: str, search_element: SearchElementTypes, limit: int = 10,
                   market: str = "from_token") -> SearchResult:
    search_res = sp.search(q=f"{search_element.value}:{query}", type=search_element.value, limit=limit)
    return SearchResult(**search_res[next(iter(search_res))])

def get_artist_albums(sp: Spotify, artist_id:str, country:str) -> list[AlbumSearchItem]:
    # todo - this does not return all the albums for reason
    #  for example - mastodon returns 6 albums while the limit here is 20
    albums_res = sp.artist_albums(artist_id=artist_id, country=country)
    return [AlbumSearchItem(**album) for album in albums_res.get("items")]


def get_album_tracks(sp: Spotify, album_id: str, country:str) -> list[TracksSearchItems]:
    tracks_res = sp.album_tracks(album_id=album_id, market=country)
    return [TracksSearchItems(**track) for track in tracks_res.get("items")]


def play_artist(sp: Spotify, artist_query, market="from_token"):
    # todo - to make the delay minimal, we need to first get the first album and tell spotify to play it
    #  then add the rest of the albums to the queue

    search_result = search_spotify(
        sp=sp,
        query=artist_query,
        search_element=SearchElementTypes.ARTIST,
        limit=1
    )

    if len(search_result.items) == 0:
        raise NoArtistFound()

    artist = search_result.get_item_by_index(0)
    albums = get_artist_albums(sp=sp, artist_id=artist.id, country=market)

    if len(albums) == 0:
        raise NoAlbumsFound()


    all_albums_tracks = []
    album_tracks = [get_album_tracks(sp=sp, album_id=album.id, country=market) for album in albums]
    for i in album_tracks:
        all_albums_tracks.extend(i)

    uris = [track.uri for track in all_albums_tracks]

    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(uris=uris, device_id=device.id)


def play_track(sp: Spotify, song_query):
    search_res = search_spotify(
        sp=sp,
        query=song_query,
        search_element=SearchElementTypes.TRACK,
        limit=1,
    )

    if len(search_res.items) == 0:
        raise NoTrackFound()

    uris = [track.uri for track in search_res.items]

    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(uris=uris, device_id=device.id)


def play_album(sp: Spotify, album_query):
    album_res = search_spotify(sp=sp, query=album_query, search_element=SearchElementTypes.ALBUM, limit=1)
    albums = album_res.items

    if len(albums) == 0:
        raise NoAlbumsFound()

    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(context_uri=albums[0].uri, device_id=device.id)


def play_or_pause_track(sp: Spotify):
    device = get_first_active_device(sp=sp)

    if device is None:
        raise NoActiveDeviceFound()

    currently_playing = sp.currently_playing()

    if currently_playing is None or not currently_playing.get("is_playing"):
        sp.start_playback(device_id=device.id)
    else:
        sp.pause_playback(device_id=device.id)


def get_current_playing_track(sp: Spotify) -> Track | None:
    track_data = sp.current_playback()

    if track_data is None:
        return None

    return Track(
        name=track_data.get("item").get("name"),
        artist=track_data.get("item").get("artists")[0].get("name"),
        album=track_data.get("item").get("album").get("name"),
        is_playing=track_data.get("is_playing"),
    )

#endregion

if __name__ == "__main__":
    _cfg = Config()
    _sp = get_spotify_client(_cfg)
    device = get_first_active_device(sp=_sp)

    print("hello")