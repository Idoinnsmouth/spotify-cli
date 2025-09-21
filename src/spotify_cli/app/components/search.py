import asyncio

from spotipy import Spotify
from textual import on
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Input, Label, RadioSet, RadioButton, Footer

from spotify_cli.spotify_service import play_artist, play_track, play_album


class SearchScreen(Screen):
    BINDINGS = [
        Binding("1", "set_mode('artist')", "1. Artists"),
        Binding("2", "set_mode('track')", "2. Tracks"),
        Binding("3", "set_mode('album')", "3. Albums"),
        Binding("escape", "pop_screen", "Close"),
    ]

    sp: Spotify
    print_error_text_to_gutter: callable
    mode = reactive("artist")

    def __init__(self, sp: Spotify, print_error_text_to_gutter: callable):
        super().__init__()
        self.input: Input | None = None
        self.sp = sp
        self.print_error_text_to_gutter = print_error_text_to_gutter

    def compose(self):
        yield Label("Search")
        yield RadioSet(
            RadioButton("Artist", id="artist", value=True),
            RadioButton("Album", id="album", value=True),
            RadioButton("Track", id="track", value=True),
            id="mode_picker",
        )
        self.input = Input(
            id="search",
            type="text",
        )
        yield self.input
        yield Footer()


    def on_mount(self):
        self._apply_mode()

    def watch_mode(self):
        self._apply_mode()

    #region ##### Events ####
    @on(Input.Submitted, "#search")
    def handle_artist_submit(self, event: Input.Submitted):
        self.input.clear()

        try:
            if self.mode == "artist":
                play_artist(
                    sp=self.sp,
                    artist_query=event.value
                )
            elif self.mode == "track":
                play_track(
                    sp=self.sp,
                    song_query=event.value
                )
            elif self.mode == "album":
                play_album(
                    sp=self.sp,
                    album_query=event.value
                )
        except Exception as e:
            self.print_error_text_to_gutter([str(e)])

        self.dismiss()
    #endregion

    #region #### Utils ####
    def _apply_mode(self):
        placeholders = {
            "artist": "Search Artist",
            "track": "Search Track",
            "album": "Search Album",
        }

        self.input.placeholder = placeholders[self.mode]

        self.input.suggester = {
            "artist": ArtistSuggester(self.sp, delay=0.3),
            "track": ArtistSuggester(self.sp, delay=0.3), # todo - create suggster
            "album": ArtistSuggester(self.sp, delay=0.3),   # todo - create suggster
        }[self.mode]

        picker = self.query_one("#mode_picker", RadioSet)
        picker.value = self.mode
        self.input.focus()
    #endregion

    #region #### Actions ####

    def on_radio_set_changed(self, event: RadioSet.Changed):
        self.mode = event.pressed.id

    def action_set_mode(self, mode: str):
        self.mode = mode

    def action_pop_screen(self):
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