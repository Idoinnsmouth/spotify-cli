from time import sleep

import pytest
import spotipy
from spotipy import Spotify
from textual.app import App, ComposeResult
from textual.widgets import LoadingIndicator, DataTable, Static

from spotify_cli.app.widgets.library import Library
from spotify_cli.core import spotify_service
from spotify_cli.tests.utils import MockSpotify, generate_test_album_search_item

spotipy.Spotify = MockSpotify


class LibraryApp(App):
    def compose(self) -> ComposeResult:
        yield Library(
            sp=Spotify()
        )


class TestLibrary:
    @pytest.mark.asyncio
    async def test_shows_loading_while_getting_albums(self, monkeypatch):
        monkeypatch.setattr(spotify_service, "get_library_albums_cached", lambda: sleep(20))
        app = LibraryApp()

        async with app.run_test():
            assert app.query_one("#albums_loading", LoadingIndicator).display == True

    @pytest.mark.asyncio
    async def test_shows_album_list_when_loaded(self, monkeypatch):
        albums = [generate_test_album_search_item("test1"), generate_test_album_search_item("test2")]
        monkeypatch.setattr(
            "spotify_cli.app.widgets.library.get_library_albums_cached",
            lambda sp: albums,
        )
        app = LibraryApp()

        async with app.run_test():
            sleep(1)
            assert app.query_one("#albums_loading", LoadingIndicator).display == False

            data_table = app.query_one(DataTable)

            assert len(data_table.rows) == 2

            assert data_table.get_row_at(0)[0] == albums[0].get_albums_artists()
            assert data_table.get_row_at(0)[1] == albums[0].name

            assert data_table.get_row_at(1)[0] == albums[1].get_albums_artists()
            assert data_table.get_row_at(1)[1] == albums[1].name


    @pytest.mark.asyncio
    async def test_show_error_when_fetching_failed(self, monkeypatch):
        monkeypatch.setattr(
            "spotify_cli.app.widgets.library.get_library_albums_cached",
            lambda sp: 2/0,
        )
        app = LibraryApp()

        async with app.run_test():
            sleep(1)
            assert app.query_one("#albums_loading", LoadingIndicator).display == False

            data_table = app.query_one(DataTable)
            assert len(data_table.rows) == 0

            static = app.query_one("#albums_error", Static)
            assert static.content == "Error: Failed loading albums, try again later"