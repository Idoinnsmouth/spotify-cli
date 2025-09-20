import asyncio

from spotipy import Spotify
from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Header, Footer, Input, Pretty

from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.playback import play_or_pause_track, play_artist


class SpotifyApp(App):
    sp: Spotify
    _debug_mode: False

    BINDINGS = [
        ("p", "pause_start_playback", "Pause/Resume Playback"),
        ("s", "show_search", "Search By Artist")
    ]


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

class SearchScreen(Screen):
    sp: Spotify
    print_error_text_to_gutter: callable

    def __init__(self, sp: Spotify, print_error_text_to_gutter: callable):
        super().__init__()
        self.sp = sp
        self.print_error_text_to_gutter = print_error_text_to_gutter

    def compose(self):
        yield Input(
            id="artist_input",
            placeholder="Artist",
            type="text",
            suggester=ArtistSuggester(sp=self.sp),
        )

    #region ##### Events ####
    @on(Input.Submitted, "#artist_input")
    def handle_artist_submit(self, event: Input.Submitted):
        self.query_one("#artist_input", Input).clear()

        try:
            play_artist(
                sp=self.sp,
                artist_query=event.value
            )
        except Exception as e:
            self.print_error_text_to_gutter([str(e)])

        self.dismiss()
    #endregion

class ArtistSuggester(Suggester):
    sp: Spotify
    delay: float
    _call_id: int

    def __init__(self, sp: Spotify, delay: float = 0.30, use_cache: bool = False):
        super().__init__(use_cache=use_cache)
        self.sp = sp
        self.delay = delay
        self._call_id = 0

    async def get_suggestion(self, value: str):
        # don't want to start suggesting based on only one char
        if len(value.strip()) < 2:
            return None

        self._call_id += 1
        my_id = self._call_id

        await asyncio.sleep(self.delay)

        if my_id != self._call_id:
            return None

        res = self.sp.search(q=f"artist:{value}", type="artist", limit=1)
        artist = res.get("artists", {}).get("items", [])
        return artist[0].get("name") if artist else None
