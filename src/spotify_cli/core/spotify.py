import subprocess
import time
from datetime import datetime
from enum import Enum
from typing import Optional

from spotipy import Spotify, SpotifyOauthError

from spotify_cli.core.auth import get_spotify_client
from spotify_cli.core.config import Config
from spotify_cli.schemas.device import Device
from spotify_cli.schemas.playback import PlaybackState
from spotify_cli.schemas.search import SearchResult, AlbumSearchItem, TracksSearchItems
from spotify_cli.schemas.track import Track, Actions
from spotify_cli.core.caching import get_saved_albums_cache_path, SavedAlbumsCache, EntryModel, SavedAlbumsModel
from spotify_cli.utils.date_time_helpers import parse_date


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


class PlatformAdapter:
    """currently this class is very simple in the future three is the possibility I'll want to
        add to this to maybe control other machines connected to the spotify client like tv's are smart speakers, etc...
    """

    @staticmethod
    def ensure_spotify_running():
        try:
            subprocess.run(["pgrep", "-x", "Spotify"], check=True, stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            subprocess.run(["open", "-a", "Spotify"])
            time.sleep(1.5)


class SpotifyClient:
    def __init__(self, sp: Spotify, platform: Optional[PlatformAdapter] = None,
                 cache: Optional[SavedAlbumsCache] = None):
        self.sp = sp
        self.platform = platform or PlatformAdapter()
        self.cache = cache or SavedAlbumsCache(get_saved_albums_cache_path())

    # region #### Factories ####
    @classmethod
    def from_config(cls, config: Config) -> "SpotifyClient":
        sp = get_spotify_client(config)
        return cls(sp=sp)

    @staticmethod
    def is_spotify_config_valid(client_id: str, client_secret: str) -> bool:
        cfg = Config()
        cfg.client_id = client_id
        cfg.client_secret = client_secret
        try:
            get_spotify_client(cfg).devices()
            return True
        except SpotifyOauthError:
            return False

    # endregion

    # region #### Devices ####
    def get_devices(self) -> list[Device]:
        resp = self.sp.devices()
        return [Device(**device) for device in resp.get("devices", [])]

    def get_first_active_device(self) -> Device | None:
        devices = self.get_devices()

        if len(devices) > 0:
            return next((_device for _device in devices if _device.is_active), None)
        else:
            return None

    async def wait_for_device(self, tries=12, delay=0.5) -> Device | None:
        for _ in range(tries):
            active_device = self.get_first_active_device()
            if active_device:
                return active_device
            time.sleep(delay)
        return None

    # endregion

    # region #### Search ####
    def search_spotify_tracks(self, query: str, search_element: SearchElementTypes,
                              limit: int = 10) -> SearchResult:
        if search_element is SearchElementTypes.ARTIST:
            # For type artist we search for tracks by artist because it's the fasted way to get as many tracks
            # as possibles by that artist
            search_res = self.sp.search(q=f"{search_element.value}:{query}", type=SearchElementTypes.TRACK.value,
                                        limit=limit)
        else:
            search_res = self.sp.search(q=f"{search_element.value}:{query}", type=search_element.value, limit=limit)
        return SearchResult(**search_res[next(iter(search_res))])

    def search_spotify_suggestions(self, query: str, search_element: SearchElementTypes, limit: int = 10,
                                   market: str = "from_token") -> SearchResult:
        """This function is to be used for the suggesters, not finding playbacks"""
        search_res = self.sp.search(q=f"{search_element.value}:{query}", type=search_element.value, limit=limit)
        return SearchResult(**search_res[next(iter(search_res))])

    async def search_artist_and_play(self, artist_query: str) -> TracksSearchItems:
        HARD_LIMIT = 50
        search_result = self.search_spotify_tracks(query=f"{artist_query}",
                                                   search_element=SearchElementTypes.ARTIST,
                                                   limit=HARD_LIMIT)

        uris: list[str] = []
        for i in search_result.items:
            uris.append(i.uri)

        await self.play_by_uris_or_context_uri(uris=uris)
        return search_result.get_item_by_index()

    async def search_track_and_play(self, song_query) -> TracksSearchItems:
        search_res = self.search_spotify_tracks(query=song_query, search_element=SearchElementTypes.TRACK, limit=1)

        if len(search_res.items) == 0:
            raise NoTrackFound()

        uris = [track.uri for track in search_res.items]

        await self.play_by_uris_or_context_uri(uris=uris)
        return search_res.get_item_by_index()

    async def search_album_and_play(self, album_query) -> TracksSearchItems:
        album_res = self.search_spotify_tracks(query=album_query, search_element=SearchElementTypes.ALBUM, limit=1)
        albums: list[AlbumSearchItem] = album_res.items

        if len(albums) == 0:
            raise NoAlbumsFound()

        await self.play_by_uris_or_context_uri(context_uri=albums[0].uri)
        returned_track = self._get_first_track_from_album_search_item(album=albums[0])
        return returned_track

    # endregion

    # region ##### Playback #####
    async def play_by_uris_or_context_uri(self, uris: list[str] = None, context_uri: str = None):
        if not uris and not context_uri:
            raise ValueError("play_by_uris_or_context_uri must be called with either uris or context_uri")

        self.platform.ensure_spotify_running()
        device = await self.wait_for_device()
        if device is None:
            raise NoActiveDeviceFound()

        self.sp.start_playback(uris=uris, context_uri=context_uri, device_id=device.id)

    def _get_first_track_from_album_search_item(self, album: AlbumSearchItem) -> TracksSearchItems:
        album_tracks = self.sp.album_tracks(album.id, limit=1)
        _album_track = album_tracks.get("items")[0]
        return TracksSearchItems(
            **_album_track,
            album=album,
        )

    # todo - currently this work but this could be written better
    def play_or_pause_track(self, active_device: Device | None = None):
        if active_device is None:
            active_device = self.get_first_active_device()

            if active_device is None:
                raise NoActiveDeviceFound()

        currently_playing = self.get_playback_state()

        if self._can_start_playback(currently_playing):
            if currently_playing.device_id != active_device.id:
                self.sp.transfer_playback(device_id=active_device.id)
            else:
                self.sp.start_playback(device_id=active_device.id)
        elif self._can_pause_playback(currently_playing):
            self.sp.pause_playback(device_id=currently_playing.device_id)

    @staticmethod
    def _can_start_playback(currently_playing: PlaybackState | None) -> bool:
        if currently_playing is None:
            return False
        if currently_playing.is_playing:
            return False
        if currently_playing.actions.disallows.resuming:
            return False

        return True

    @staticmethod
    def _can_pause_playback(currently_playing: PlaybackState | None) -> bool:
        if currently_playing is None:
            return False
        if currently_playing.actions.disallows.pausing:
            return False
        return True

    def get_playback_state(self) -> PlaybackState | None:
        playback_data = self.sp.current_playback()

        if playback_data is None:
            return None

        # todo - make track schema more like the result from spotify
        track = Track(
            name=playback_data.get("item").get("name"),
            artist=playback_data.get("item").get("artists")[0].get("name"),
            album=AlbumSearchItem(
                **playback_data.get("item").get("album")
            ),
            is_playing=playback_data.get("is_playing"),
            device=Device(**playback_data.get("device")),
            actions=Actions(**playback_data.get("actions"))
        )

        return PlaybackState.to_state(playback_data)

    # endregion

    # region #### Library ####
    def get_library_albums_cached(
            self,
            ttl_sec: int = 900,
    ) -> list[AlbumSearchItem]:
        cache = SavedAlbumsCache(get_saved_albums_cache_path())
        model = cache.load() or cache.default_payload()

        now = time.time()
        if len(model.album_ids) > 0 and model.updated_ts and (now - model.updated_ts < ttl_sec):
            # Cache is fresh by TTL—return as is.
            return [entry.album for entry in model.entries]

        newest_added_at = self._get_newest_added_album_in_library()

        if newest_added_at and newest_added_at == model.latest_added_at:
            # No change since last seen—refresh TTL and return
            model.updated_ts = now
            cache.save(model)
            return [entry.album for entry in model.entries]

        new_entries = self._get_new_library_entries(known_ids=model.album_ids)

        if new_entries:
            model.entries = [entry for entry in new_entries] + model.entries
            model.album_ids = list(set(model.album_ids).union(a.album.id for a in new_entries))
            model.latest_added_at = newest_added_at or model.latest_added_at

        model.updated_ts = now
        model.entries.sort(key=lambda e: e.added_at, reverse=True)

        cache.save(model)
        return [entry.album for entry in model.entries]

    def _get_new_library_entries(self, known_ids: list[str]) -> list[EntryModel]:
        """
        go overs the user library in batches and add new saved albums to the model until hitting an id of
        existing model in the library
        """
        known_ids = set(known_ids)
        new_entries: list[EntryModel] = []

        offset = 0
        while True:
            BATCH = 50
            res = self.sp.current_user_saved_albums(limit=BATCH, offset=offset)

            def key(item):
                added = parse_date(item.get("added_at"))
                release = parse_date(item.get("release_date"))
                # if release is after added → use release as effective sort key
                return release if release > added else added

            items = sorted(res.get("items", []), key=key, reverse=True)
            if not items:
                break

            hit_known = False
            for it in items:
                release_date = it.get("release_date", None)
                added_at = it.get("added_at")
                album = it.get("album", {})
                album_id = album.get("id")

                if self._is_album_not_released_yet(added_date=added_at, release_date=release_date):
                    # we don't save pre-saved albums to the cache because we can't play them on the app,
                    # and it causes headache later when trying to update cache when they release
                    continue

                if album_id in known_ids:
                    hit_known = True
                    break

                new_entries.append(EntryModel(
                    album=AlbumSearchItem(**album),
                    added_at=added_at
                ))

            # Stop if we reached previously known territory or the last page
            if hit_known or len(items) < BATCH:
                break

            offset += BATCH

        return new_entries

    def _get_newest_added_album_in_library(self):
        # Freshness peek: get the newest 'added_at' from API
        peek = self.sp.current_user_saved_albums(limit=1, offset=0)
        peek_items = peek.get("items", [])
        return peek_items[0]["added_at"] if peek_items else None

    @staticmethod
    def _is_album_not_released_yet(added_date: str, release_date: Optional[str]) -> bool:
        if release_date is None:
            return False

        try:
            added_dt = datetime.fromisoformat(added_date.replace("Z", "+00:00"))
        except ValueError:
            added_dt = datetime.strptime(added_date, "%Y-%m-%d")

        try:
            release_dt = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
        except ValueError:
            # If only date provided, assume midnight UTC
            release_dt = datetime.strptime(release_date, "%Y-%m-%d")

        return added_dt < release_dt

    # endregion


if __name__ == "__main__":
    _cfg = Config()
    _sp = get_spotify_client(_cfg)
    instance = SpotifyClient(
        sp=_sp
    )

    instance.get_library_albums_cached()
