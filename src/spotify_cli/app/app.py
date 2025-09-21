import asyncio

from spotipy import Spotify
from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Header, Footer, Input, Pretty

from spotify_cli.app.components.search import SearchScreen
from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.spotify_service import play_or_pause_track, play_artist


class SpotifyApp(App):
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        ("p", "pause_start_playback", "Pause/Resume"),
        ("s", "show_search", "Search")
    ]


    sp: Spotify
    _debug_mode: False


    def compose(self) -> ComposeResult:
        # todo - change this before release (:
        self._debug_mode = True
        self.sp = get_spotify_client(Config())

        if self._debug_mode:
            yield Pretty(
                [],
                id="debug_gutter"
            )
        yield Footer()

    #region #### Actions ####
    def action_pause_start_playback(self):
        play_or_pause_track(sp=self.sp)

    def action_show_search(self):
        self.push_screen(SearchScreen(sp=self.sp, print_error_text_to_gutter=self.print_error_text_to_gutter))
    #endregion

    #region #### Utils ####
    def print_error_text_to_gutter(self, errors: list[str]):
        if self._debug_mode:
            gutter = self.query_one("#debug_gutter", Pretty)
            gutter.update(errors)
    #endregion


