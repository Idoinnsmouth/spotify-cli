import asyncio
from functools import lru_cache
from operator import attrgetter
from time import sleep

from spotipy import Spotify
from textual import on
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import Screen
from textual.suggester import Suggester
from textual.widgets import Input, Label, RadioSet, RadioButton, Footer

from spotify_cli.schemas.search import TracksSearchItems, SearchResult
from spotify_cli.spotify_service import search_artist_and_play, search_track_and_play, search_album_and_play, \
    search_spotify_tracks, SearchElementTypes, \
    get_current_playing_track, search_spotify_suggestions


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

    # region ##### Events ####
    @on(Input.Submitted, "#search")
    def handle_artist_submit(self, event: Input.Submitted) -> TracksSearchItems | None:
        track = None
        self.input.clear()

        try:
            if self.mode == "artist":
                track = search_artist_and_play(
                    sp=self.sp,
                    artist_query=event.value
                )
            elif self.mode == "track":
                track = search_track_and_play(sp=self.sp, song_query=event.value)
            elif self.mode == "album":
                track = search_album_and_play(sp=self.sp, album_query=event.value)
        except Exception as e:
            self.print_error_text_to_gutter([str(e)])

        self.dismiss(track)

    # endregion

    # region #### Utils ####
    def _apply_mode(self):
        placeholders = {
            "artist": "Search Artist",
            "track": "Search Track",
            "album": "Search Album",
        }

        self.input.placeholder = placeholders[self.mode]

        self.input.suggester = {
            "artist": SearchSuggester(self.sp, delay=0.3, search_element_type=SearchElementTypes.ARTIST),
            "track": SearchSuggester(self.sp, delay=0.3, search_element_type=SearchElementTypes.TRACK),
            "album": SearchSuggester(self.sp, delay=0.3, search_element_type=SearchElementTypes.ALBUM),
        }[self.mode]

        picker = self.query_one("#mode_picker", RadioSet)
        picker.value = self.mode
        self.input.focus()

    # endregion

    # region #### Actions ####

    def on_radio_set_changed(self, event: RadioSet.Changed):
        self.mode = event.pressed.id

    def action_set_mode(self, mode: str):
        self.mode = mode

    def action_pop_screen(self):
        self.dismiss()
    # endregion


class SearchSuggester(Suggester):
    sp: Spotify
    search_element_type: SearchElementTypes
    delay: float
    _call_id: int
    _last_value: str | None

    def __init__(self, sp: Spotify, search_element_type: SearchElementTypes, delay: float = 0.30,
                 use_cache: bool = False):
        super().__init__(use_cache=use_cache)
        self.sp = sp
        self.delay = delay
        self._call_id = 0
        self._last_value = None
        self.search_element_type = search_element_type

    async def get_suggestion(self, value: str) -> str | None:
        # don't want to start suggesting based on only one char
        v = value.strip()
        if len(v) < 2:
            return None

        if v == self._last_value:
            return None
        self._last_value = v

        self._call_id += 1
        my_id = self._call_id

        await asyncio.sleep(self.delay)
        if my_id != self._call_id:
            return None

        # run blocking Spotipy call off the event loop
        try:
            res: SearchResult | None = await asyncio.wait_for(
                asyncio.to_thread(self._search_spotify_cached, v, self.search_element_type, self.sp),
                timeout=2.5,
            )
        except Exception as e:
            # ignore errors in suggester path to keep typing smooth
            return None

        # if a newer keystroke arrived while we waited, drop this result
        if my_id != self._call_id:
            return None

        if res is None or res.total == 0:
            return None

        top_result = max(res.items, key=lambda i: getattr(i, 'popularity', 0))
        return top_result.name

    @staticmethod
    @lru_cache(maxsize=256)
    def _search_spotify_cached(v: str, element_type: SearchElementTypes, sp: Spotify) -> SearchResult | None:
        # in results album have no popularity so there is no way to get the top result as in spotify app
        search_limit = 1 if element_type is SearchElementTypes.ALBUM else 10
        return search_spotify_suggestions(sp=sp, query=v, search_element=element_type, limit=search_limit)
