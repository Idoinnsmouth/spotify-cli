from textual.containers import Container

from spotipy import Spotify
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable

from spotify_cli.schemas.search import AlbumSearchItem


class Library(Widget):
    albums: reactive[list[AlbumSearchItem]] = reactive([])
    TABLE_COL = ("artist", "album")

    def __init__(self, sp: Spotify):
        super().__init__()
        self.sp = sp

    def compose(self):
        with Container(id="album_table"):
            yield DataTable()

    def on_mount(self):
        dt = self.query_one(DataTable)
        dt.cursor_type = "row"

    def watch_albums(self, old: list[AlbumSearchItem], new: list[AlbumSearchItem]):
        if old == new:
            return

        dt = self.query_one(DataTable)
        dt.add_columns(*self.TABLE_COL)

        for album in new:
            dt.add_row(album.get_albums_artists(), album.name, key=album.uri)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected):
        self.sp.start_playback(context_uri=event.row_key.value)
