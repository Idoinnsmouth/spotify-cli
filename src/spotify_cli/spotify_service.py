import asyncio
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
from spotify_cli.utils.caching import cache_path, load_cache, new_cache, save_cache


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
def search_spotify_tracks(sp: Spotify, query: str, search_element: SearchElementTypes, limit: int = 10) -> SearchResult:
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


def search_artist_and_play(sp: Spotify, artist_query) -> TracksSearchItems:
    HARD_LIMIT = 50
    search_result = search_spotify_tracks(sp=sp, query=f"{artist_query}",
                                          search_element=SearchElementTypes.ARTIST,
                                          limit=HARD_LIMIT)

    uris: list[str] = []
    for i in search_result.items:
        uris.append(i.uri)

    play_by_uris_or_context_uri(sp=sp, uris=uris)
    return search_result.get_item_by_index()


def search_track_and_play(sp: Spotify, song_query) -> TracksSearchItems:
    search_res = search_spotify_tracks(sp=sp, query=song_query, search_element=SearchElementTypes.TRACK, limit=1)

    if len(search_res.items) == 0:
        raise NoTrackFound()

    uris = [track.uri for track in search_res.items]

    play_by_uris_or_context_uri(sp=sp, uris=uris)
    return search_res.get_item_by_index()


def search_album_and_play(sp: Spotify, album_query) -> TracksSearchItems:
    album_res = search_spotify_tracks(sp=sp, query=album_query, search_element=SearchElementTypes.ALBUM, limit=1)
    albums: list[AlbumSearchItem] = album_res.items

    if len(albums) == 0:
        raise NoAlbumsFound()

    play_by_uris_or_context_uri(sp=sp, context_uri=albums[0].uri)
    returned_track = _get_first_track_from_album_search_item(sp=sp, album=albums[0])
    return returned_track


def play_by_uris_or_context_uri(sp: Spotify, uris: list[str] = None, context_uri: str = None):
    ensure_spotify_running()
    device = wait_for_device(sp)
    if device is None:
        raise NoActiveDeviceFound()

    sp.start_playback(uris=uris, context_uri=context_uri, device_id=device.id)


def _get_first_track_from_album_search_item(sp: Spotify, album: AlbumSearchItem) -> TracksSearchItems:
    album_tracks = sp.album_tracks(album.id, limit=1)
    _album_track = album_tracks.get("items")[0]
    return TracksSearchItems(
        **_album_track,
        is_playable=True,
        album=album,
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

#### Library ####
def get_library_albums_cached(
        sp: Spotify,
        ttl_sec: int = 900,
) -> list[AlbumSearchItem]:
    path = cache_path()
    cache = load_cache(path) or new_cache()

    now = time.time()
    if cache.get("updated_ts") and (now - cache.get("updated_ts") < ttl_sec):
        # Cache is fresh by TTL—return as is.
        return [entry["album"] for entry in cache["entries"]]

    # Freshness peek: get the newest 'added_at' from API
    peek = sp.current_user_saved_albums(limit=1, offset=0)
    peek_items = peek.get("items", [])
    newest_added_at = peek_items[0]["added_at"] if peek_items else None

    if newest_added_at and newest_added_at == cache["latest_added_at"]:
        # No change since last seen—refresh TTL and return
        cache["updated_ts"] = now
        save_cache(path, cache)
        return [entry["album"] for entry in cache["entries"]]

    # There are changes or first load: delta-fetch
    known_ids = set(cache["album_ids"])
    new_entries: list[dict] = []

    offset = 0
    while True:
        BATCH = 50
        res = sp.current_user_saved_albums(limit=BATCH, offset=offset)
        items = res.get("items", [])
        if not items:
            break

        hit_known = False
        for it in items:
            added_at = it.get("added_at")
            album = it.get("album", {})
            album_id = album.get("id")

            if album_id in known_ids:
                hit_known = True
                break

            new_entries.append({"added_at": added_at, "album": AlbumSearchItem(**album)})

        # Stop if we reached previously known territory or the last page
        if hit_known or len(items) < BATCH:
            break

        offset += BATCH

    if new_entries:
        cache["entries"] = [entry for entry in new_entries] + cache["entries"]
        cache["album_ids"] = list(set(cache["album_ids"]).union(a["album"].id for a in new_entries))
        cache["latest_added_at"] = newest_added_at or cache["latest_added_at"]

    cache["updated_ts"] = now
    cache["entries"].sort(key=lambda e: e["added_at"], reverse=True)

    save_cache(path, cache)
    return [entry["album"] for entry in cache["entries"]]


if __name__ == "__main__":
    _cfg = Config()
    _sp = get_spotify_client(_cfg)
    _res = get_library_albums_cached(sp=_sp)

    # play_or_pause_track(sp=_sp, active_device=_devices[0])
    print("hello")
