import subprocess
import threading
import time
from enum import Enum
from queue import Queue

from spotipy import Spotify

from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.schemas.device import Device
from spotify_cli.schemas.search import SearchResult, AlbumSearchItem, TracksSearchItems
from spotify_cli.schemas.track import Track, Actions


class SearchElementTypes(Enum):
    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"


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


# region #### Check Spotify client ####

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


def get_first_active_device(sp) -> Device | None:
    devices = get_devices(sp=sp)

    if len(devices) > 0:
        return next((_device for _device in devices if _device.is_active), devices[0])
    else:
        return None


# todo - turn this to async func
def wait_for_device(sp, tries=12, delay=0.5) -> Device | None:
    for _ in range(tries):
        active_device = get_first_active_device(sp)
        if active_device:
            return active_device
        time.sleep(delay)
    return None


# endregion

# region #### Playback ####
def search_spotify_tracks(sp: Spotify, query: str, search_element: SearchElementTypes, limit: int = 10,
                   market: str = "from_token") -> SearchResult:
    if search_element is SearchElementTypes.ARTIST:
        # For type artist we search for tracks by artist because it's the fasted way to get as many tracks
        # as possibles by that artist
        search_res = sp.search(q=f"{search_element.value}:{query}", type=SearchElementTypes.TRACK.value, limit=limit)
    else:
        search_res = sp.search(q=f"{search_element.value}:{query}", type=search_element.value, limit=limit)
    return SearchResult(**search_res[next(iter(search_res))])


def search_spotify_suggestions(sp: Spotify, query: str, search_element: SearchElementTypes, limit: int = 10,
                   market: str = "from_token") -> SearchResult:
    """This function is to be used for the suggesters, not finding playbacks"""
    search_res = sp.search(q=f"{search_element.value}:{query}", type=search_element.value, limit=limit)
    return SearchResult(**search_res[next(iter(search_res))])


def play_artist(sp: Spotify, artist_query, market="from_token") -> TracksSearchItems:
    HARD_LIMIT = 50
    search_result = search_spotify_tracks(sp=sp, query=f"{artist_query}", search_element=SearchElementTypes.ARTIST,
                                          limit=HARD_LIMIT)

    uris: list[str] = []
    for i in search_result.items:
        uris.append(i.uri)

    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(uris=uris, device_id=device.id)
    return search_result.items[0]


def play_track(sp: Spotify, song_query) -> TracksSearchItems:
    search_res = search_spotify_tracks(sp=sp, query=song_query, search_element=SearchElementTypes.TRACK, limit=1)

    if len(search_res.items) == 0:
        raise NoTrackFound()

    uris = [track.uri for track in search_res.items]

    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(uris=uris, device_id=device.id)

    return search_res.get_item_by_index()


def play_album(sp: Spotify, album_query) -> TracksSearchItems:
    album_res = search_spotify_tracks(sp=sp, query=album_query, search_element=SearchElementTypes.ALBUM, limit=1)
    albums = album_res.items

    if len(albums) == 0:
        raise NoAlbumsFound()

    returned_track = Queue()
    thread = threading.Thread(
        target=_get_first_track_from_album_search_item,
        args=(sp, albums[0], returned_track)
    )
    thread.start()

    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(context_uri=albums[0].uri, device_id=device.id)
    thread.join()
    return returned_track.get()


def _get_first_track_from_album_search_item(sp: Spotify, album: AlbumSearchItem, returned_track: Queue):
    album_tracks = sp.album_tracks(album.id, limit=1)
    _album_track = album_tracks.get("items")[0]
    returned_track.put(
        TracksSearchItems(
            **_album_track,
            is_playable=True,
            album=album,
        )
    )


# todo - currently this work but this could be written better
def play_or_pause_track(sp: Spotify, active_device: Device | None = None):
    if active_device is None:
        active_device = get_first_active_device(sp=sp)

        if active_device is None:
            raise NoActiveDeviceFound()

    currently_playing = get_current_playing_track(sp=sp)

    if _can_start_playback(currently_playing, active_device):
        if currently_playing.device.id != active_device.id:
            sp.transfer_playback(active_device.id)
        else:
            sp.start_playback(device_id=active_device.id)
    elif _can_pause_playback(currently_playing, active_device):
        if currently_playing.device.id != active_device.id:
            sp.transfer_playback(active_device.id)
        else:
            sp.pause_playback(device_id=active_device.id)


# todo - maybe load currently playing into a schema and make this a function
def _can_start_playback(currently_playing: Track | None, active_device: Device | None) -> bool:
    if currently_playing is None:
        return False
    if currently_playing.is_playing is True:
        return False
    if currently_playing.actions.disallows.resuming is True:
        return False

    return True


def _can_pause_playback(currently_playing: Track | None, active_device: Device | None) -> bool:
    if currently_playing is None:
        return False
    if currently_playing.actions.disallows.pausing is True:
        return False
    return True


def get_current_playing_track(sp: Spotify) -> Track | None:
    track_data = sp.current_playback()

    if track_data is None:
        return None

    # todo - make track schema more like the result from spotify
    return Track(
        name=track_data.get("item").get("name"),
        artist=track_data.get("item").get("artists")[0].get("name"),
        album=AlbumSearchItem(
            **track_data.get("item").get("album")
        ),
        is_playing=track_data.get("is_playing"),
        device=Device(**track_data.get("device")),
        actions=Actions(**track_data.get("actions"))
    )


# endregion

if __name__ == "__main__":
    _cfg = Config()
    _sp = get_spotify_client(_cfg)
    _res = play_artist(sp=_sp, artist_query="type o negative")

    # play_or_pause_track(sp=_sp, active_device=_devices[0])
    print("hello")
