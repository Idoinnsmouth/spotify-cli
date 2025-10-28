import asyncio
import datetime
from typing import Optional, Any, Callable

from pydantic import ValidationError
from spotipy import Spotify, SpotifyException
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Pretty

from spotify_cli.app.screens.choose_device import ChooseDevice
from spotify_cli.app.widgets.active_device import ActiveDevice
from spotify_cli.app.widgets.library import Library
from spotify_cli.app.screens.search import SearchScreen
from spotify_cli.app.widgets.track_details import TrackDetail
from spotify_cli.schemas.device import Device
from spotify_cli.schemas.playback import PlaybackState
from spotify_cli.schemas.search import TracksSearchItems
from spotify_cli.schemas.track import Track


class ScreenChange(Message):
    def __init__(self, screen: type[Screen], params: dict[str, Any], callback: Optional[Callable]):
        self.screen = screen
        self.params = params
        self.callback = callback
        super().__init__()


class Main(Screen):
    BINDINGS = [
        ("p", "pause_start_playback", "Pause/Resume"),
        ("s", "show_search", "Search"),
        ("d", "show_change_device_screen", "Change Device"),
    ]

    #### Playback Polling config ####
    # in seconds
    POLL_PLAYING = 5.0
    POLL_PAUSED = 10.0
    POLL_IDLE = 25.0
    MAX_POLL_IDLE_OR_PAUSED_TIME = 3600

    active_device: reactive[Device | None] = reactive(default=None)
    cur_track: Track | None
    _debug_mode = False
    _debug_message = reactive([])
    _cancelable_sleep = None
    _first_instance_of_paused_or_idle_playback_poll: Optional[datetime] = None
    _loading = False

    def __init__(self):
        super().__init__()
        self._debug_mode = False
        self._poll_interval = self.POLL_IDLE
        self._last: PlaybackState | None = None
        self._stop = False

        self.active_device = self.app.service.get_first_active_device()
        playback_state = self.app.service.get_playback_state()
        self.cur_track = playback_state.track if playback_state else playback_state

    def on_mount(self) -> None:
        self.run_worker(self._poll_loop, thread=True, exclusive=True, group="pollers")

    async def on_unmount(self) -> None:
        self._stop = True

        if self._cancelable_sleep:
            self._cancelable_sleep.cancel()

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            with Vertical(id="track_details"):
                yield TrackDetail(track=self.cur_track)
                yield Library()

            with Container(id="devices"):
                yield ActiveDevice(active_device_name=self.active_device.name if self.active_device else None)

        if self._debug_mode:
            yield Pretty(
                self._debug_message,
                id="debug_gutter"
            )
        yield Footer()

    # region #### Actions ####
    def action_pause_start_playback(self):
        self.app.service.play_or_pause_track(active_device=self.active_device)

    def action_show_search(self):
        self.post_message(
            ScreenChange(
                SearchScreen,
                {
                    "print_error_text_to_gutter": self.print_error_text_to_gutter
                },
                self._after_search
            )
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
        self.post_message(
            ScreenChange(
                ChooseDevice,
                {"active_device": self.active_device},
                self.check_choose_device
            )
        )

    def check_choose_device(self, device: Device | None):
        self.change_active_device(device)

    # endregion

    # region #### Utils ####
    def update_track(self, track: Track | None):
        if track is None:
            return

        track_details = self.query_one(TrackDetail)
        track_details.track = track

    def change_active_device(self, device: Device):
        if not device:
            return

        self.active_device = device
        self.query_one(ActiveDevice).active_device_name = device.name
        self.app.service.play_or_pause_track(active_device=device)

    def print_error_text_to_gutter(self, errors: list[str]):
        if self._debug_mode:
            self._debug_message = errors
            gutter = self.query_one("#debug_gutter", Pretty)
            gutter.update(errors)

    async def _poll_loop(self) -> None:
        _is_idle_or_paused = False

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
                    self._first_instance_of_paused_or_idle_playback_poll = None

                    # poll faster near track end to catch seamless transitions
                    delay = max(0.8, min(base, remaining - 0.3)) if remaining > 1 else 0.8
                elif state.device_id:
                    delay = self.POLL_PAUSED
                    _is_idle_or_paused = True
                else:
                    delay = self.POLL_IDLE
                    _is_idle_or_paused = True
            else:
                delay = self.POLL_IDLE
                _is_idle_or_paused = True

            if _is_idle_or_paused:
                self._cancel_polling_if_long_pause_or_idle()

            # This is calling a custom task with sleep so it could be canceled on unmount and clear the terminal
            # right away instead of waiting for the sleep timer to run out
            self._cancelable_sleep = asyncio.create_task(self._cancelable_asyncio_sleep(delay))

    @staticmethod
    async def _cancelable_asyncio_sleep(delay: float):
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
            return self.app.service.get_playback_state(), None
        except Exception as e:
            retry_after = _safe_get_retry_after(e)
            if retry_after is not None:
                return None, retry_after
            # network hiccup—back off a bit
            return None, 2.0

    def _cancel_polling_if_long_pause_or_idle(self):
        now = datetime.datetime.now()

        if self._first_instance_of_paused_or_idle_playback_poll is None:
            self._first_instance_of_paused_or_idle_playback_poll = now
            return
        else:
            delta = now - self._first_instance_of_paused_or_idle_playback_poll
            if delta.seconds >= self.MAX_POLL_IDLE_OR_PAUSED_TIME:
                self._stop = True
    # endregion
