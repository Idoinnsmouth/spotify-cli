import asyncio

from spotipy import Spotify
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Header, Footer, Input, Pretty, Placeholder

from spotify_cli.app.components.search import SearchScreen
from spotify_cli.app.components.track_details import TrackDetail
from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.schemas.track import Track
from spotify_cli.spotify_service import play_or_pause_track, play_artist


class SpotifyApp(App):
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        ("p", "pause_start_playback", "Pause/Resume"),
        ("s", "show_search", "Search"),
        ("q", "quit", "Quit"),
    ]

    sp: Spotify
    _debug_mode: False


    def compose(self) -> ComposeResult:
        # todo - change this before release (:
        self._debug_mode = True
        self.sp = get_spotify_client(Config())


        yield Container(
            TrackDetail(),
            id="track_details"
        )

        if self._debug_mode:
            yield Pretty(
                [],
                id="debug_gutter"
            )
        yield Footer()

    #region #### Watch ####
    # def watch_track(self):

    #endregion

    #region #### Actions ####
    def action_pause_start_playback(self):
        play_or_pause_track(sp=self.sp)

    def action_show_search(self):
        self.push_screen(
            SearchScreen(
                sp=self.sp,
                print_error_text_to_gutter=self.print_error_text_to_gutter,
                update_track=self.update_track,
            )
        )

    def action_quit(self):
        # todo - pause track on exist
        self.exit()
    #endregion

    #region #### Utils ####
    def update_track(self, track: Track):
        # todo - make this not suck
        track_details = self.query_one("#track_details", Container)
        track_details.children[0].track = track

    def print_error_text_to_gutter(self, errors: list[str]):
        if self._debug_mode:
            gutter = self.query_one("#debug_gutter", Pretty)
            gutter.update(errors)
    #endregion


