import asyncio
import time
from time import sleep

from pydantic import ValidationError
from spotipy import Spotify, SpotifyException
from textual import on, log, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widget import Widget, AwaitMount
from textual.widgets import Header, Footer, Input, Pretty, Placeholder, Static

from spotify_cli.app.components.choose_device import ChooseDevice
from spotify_cli.app.components.search import SearchScreen
from spotify_cli.app.components.track_details import TrackDetail
from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.schemas.device import Device
from spotify_cli.schemas.playback import PlaybackState
from spotify_cli.schemas.search import TracksSearchItems
from spotify_cli.schemas.track import Track
from spotify_cli.spotify_service import play_or_pause_track, play_artist, get_devices, get_first_active_device, \
    get_current_playing_track


class SpotifyApp(App):
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        ("p", "pause_start_playback", "Pause/Resume"),
        ("s", "show_search", "Search"),
        ("d", "show_change_device_screen", "Change Device"),
        ("q", "quit", "Quit"),
    ]

    #### Playback Polling config ####
    # in seconds
    POLL_PLAYING = 5.0
    POLL_PAUSED = 10.0
    POLL_IDLE = 25.0

    sp: Spotify
    active_device: reactive[Device | None] = reactive(default=None)
    cur_track: Track | None
    _debug_mode: False
    _debug_message = reactive([])

    def __init__(self):
        super().__init__()
        # todo - change this before release (:
        self._debug_mode = True
        self.sp = get_spotify_client(Config())
        self.active_device = get_first_active_device(sp=self.sp)
        self.cur_track = get_current_playing_track(sp=self.sp)
        self._poll_interval = self.POLL_IDLE
        self._last: PlaybackState | None = None
        self._stop = False

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self.run_worker(self._poll_loop, thread=True, exclusive=True, group="pollers")

    async def on_unmount(self) -> None:
        self._stop = True

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            with Container(id="track_details"):
                yield TrackDetail(track=self.cur_track)

            with Container(id="devices"):
                yield ActiveDevice(active_device_name=self.active_device.name if self.active_device else None)

        if self._debug_mode:
            yield Pretty(
                self._debug_message,
                id="debug_gutter"
            )
        yield Footer()

    # region #### Watch ####
    # def watch_active_device(self):

    # endregion

    # region #### Actions ####
    def action_pause_start_playback(self):
        play_or_pause_track(sp=self.sp, active_device=self.active_device)

    def action_show_search(self):
        self.push_screen(
            SearchScreen(
                sp=self.sp,
                print_error_text_to_gutter=self.print_error_text_to_gutter,
            ),
            self._after_search
        )

    def _after_search(self, track: TracksSearchItems):
        if track is None:
            return
        self.get_and_update_track_after_search_dismiss(track)

    @work(exclusive=True, thread=True, exit_on_error=True)
    async def get_and_update_track_after_search_dismiss(self, track: TracksSearchItems):
        try:
            _track = Track(
                name=track.name,
                artist=track.artists[0].name,
                album=track.album,
                device=self.active_device,
                is_playing=True,
                actions=None
            )
        except ValidationError as e:
            raise e
        except Exception as e:
            self.print_error_text_to_gutter([str(e)])
            return

        self.update_track(_track)

    def action_show_change_device_screen(self):
        self.push_screen(
            ChooseDevice(sp=self.sp, active_device=self.active_device),
            self.check_choose_device
        )

    def check_choose_device(self, device: Device | None):
        self.change_active_device(device)

    def action_quit(self):
        # todo - pause track on exist
        self.exit()

    # endregion

    # region #### Utils ####
    def update_track(self, track: Track | None):
        if track is None:
            return

        # todo - make this not suck
        track_details = self.query_one("#track_details", Container)
        track_details.children[0].track = track

    def change_active_device(self, device: Device):
        if not device:
            return

        self.active_device = device
        self.query_one(ActiveDevice).active_device_name = device.name
        play_or_pause_track(sp=self.sp, active_device=device)

    def print_error_text_to_gutter(self, errors: list[str]):
        if self._debug_mode:
            self._debug_message = errors
            gutter = self.query_one("#debug_gutter", Pretty)
            gutter.update(errors)

    async def _poll_loop(self) -> None:
        while not self._stop:
            state, retry_after = self._safe_fetch_playback()

            if retry_after is not None:
                await asyncio.sleep(retry_after)
                continue

            if state:
                if state != self._last:
                    self._last = state
                    self.update_track(state.track)

                # adaptive sleep based on current state
                if state.is_playing and state.progress_ms and state.duration_ms:
                    remaining = (state.duration_ms - state.progress_ms) / 1000.0
                    base = self.POLL_PLAYING

                    # poll faster near track end to catch seamless transitions
                    delay = max(0.8, min(base, remaining - 0.3)) if remaining > 1 else 0.8
                elif state.device_id:
                    delay = self.POLL_PAUSED
                else:
                    delay = self.POLL_IDLE
            else:
                delay = self.POLL_IDLE

            await asyncio.sleep(delay)

    def _safe_fetch_playback(self):
        def _safe_get_retry_after(e: Exception) -> float | None:
            if isinstance(e, SpotifyException) and e.http_status == 429:
                retry = e.headers.get("Retry-After") if hasattr(e, "headers") and e.headers else None
                try:
                    return float(retry)
                except Exception:
                    return 2.0
            return None

        try:
            payload = self.sp.current_playback()
            return PlaybackState.to_state(payload), None
        except Exception as e:
            raise (e)  # remove this when you fill safe about the re-trie calls
            retry_after = _safe_get_retry_after(e)
            if retry_after is not None:
                return None, retry_after
            # network hiccup—back off a bit
            return None, 2.0
    # endregion


class ActiveDevice(Widget):
    active_device_name: reactive[str | None] = reactive(default=None)

    def __init__(self, active_device_name: str | None):
        super().__init__()
        self.active_device_name = active_device_name

    def render(self) -> str:
        if self.active_device_name:
            return f"Active Device: {self.active_device_name}"
        else:
            return "No Active device"
