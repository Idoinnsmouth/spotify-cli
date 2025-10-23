from logging import exception

from textual import work, log, on
from textual.containers import Container

from spotipy import Spotify
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, LoadingIndicator, Static

from spotify_cli.schemas.search import AlbumSearchItem
from spotify_cli.core.spotify_service import play_by_uris_or_context_uri, get_library_albums_cached


class AlbumsLoaded(Message):
    def __init__(self, albums: list[AlbumSearchItem]) -> None:
        self.albums = albums
        super().__init__()


class AlbumsFailed(Message):
    def __init__(self, error: str) -> None:
        self.error = error
        super().__init__()


class Library(Widget):
    TABLE_COL = ("artist", "album")

    def __init__(self, sp: Spotify):
        super().__init__()
        self.sp = sp

    def compose(self):
        with Container(id="album_table"):
            yield LoadingIndicator(id="albums_loading")
            yield DataTable()
            yield Static("", id="albums_error")

    def on_mount(self):
        self.query_one(DataTable).cursor_type = "row"
        self._load_albums_worker()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        play_by_uris_or_context_uri(sp=self.sp, context_uri=event.row_key.value)

    @work(thread=True, exclusive=True, group="io-albums")
    def _load_albums_worker(self):
        try:
            albums = get_library_albums_cached(sp=self.sp)
            self.post_message(AlbumsLoaded(albums))
        except Exception:
            self.post_message(AlbumsFailed("Failed loading albums, try again later"))

    @on(AlbumsLoaded)
    def _handle_albums_loaded(self, message: AlbumsLoaded):
        dt = self.query_one(DataTable)
        dt.clear()

        dt.add_columns(*self.TABLE_COL)

        for album in message.albums:
            dt.add_row(album.get_albums_artists(), album.name, key=album.uri)

        self.query_one("#albums_loading", LoadingIndicator).display = False
        self.query_one("#albums_error", Static).update("")

    @on(AlbumsFailed)
    def _handle_albums_failed(self, message: AlbumsFailed):
        self.query_one("#albums_loading", LoadingIndicator).display = False
        self.query_one("#albums_error", Static).update(f"Error: {message.error}")
