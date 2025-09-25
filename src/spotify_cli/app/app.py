import asyncio
from time import sleep

from pydantic import ValidationError
from spotipy import Spotify
from textual import on, log, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
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
        ("d", "show_change_device_screen", "Chance Device"),
        ("q", "quit", "Quit"),
    ]

    sp: Spotify
    active_device: reactive[Device | None] = reactive(default=None)
    cur_track: Track | None
    _debug_mode: False

    def __init__(self):
        super().__init__()
        # todo - change this before release (:
        self._debug_mode = True
        self.sp = get_spotify_client(Config())
        self.active_device = get_first_active_device(sp=self.sp)
        self.cur_track = get_current_playing_track(sp=self.sp)

    def on_mount(self) -> None:
        self.theme = "tokyo-night"

    def compose(self) -> ComposeResult:
        with Container(id="main"):
            with Container(id="track_details"):
                yield TrackDetail(track=self.cur_track)

            with Container(id="devices"):
                yield ActiveDevice(active_device_name=self.active_device.name if self.active_device else None)

        if self._debug_mode:
            yield Pretty(
                [],
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
            gutter = self.query_one("#debug_gutter", Pretty)
            gutter.update(errors)
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
