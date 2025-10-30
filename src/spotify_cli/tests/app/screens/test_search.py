from unittest.mock import MagicMock

import pytest
from textual.app import App
from textual.widgets import Input

from spotify_cli.app.screens.search import SearchScreen
from spotify_cli.core.spotify import SpotifyClient
from spotify_cli.tests.utils import MockSpotify


class SearchApp(App):
    def __init__(self):
        super().__init__()
        self.service = SpotifyClient(
            sp=MockSpotify,
        )

    def on_mount(self):
        self.push_screen(SearchScreen(
            print_error_text_to_gutter=lambda _: ""
        ))


class TestSearch:
    @pytest.mark.asyncio
    async def test_changes_search_mode(self, monkeypatch):
        app = SearchApp()
        async with app.run_test() as pilot:
            assert app.screen.mode == "artist"

            await pilot.click("#album")
            assert app.screen.mode == "album"

            await pilot.click("#track")
            assert app.screen.mode == "track"

            await pilot.click("#artist")
            assert app.screen.mode == "artist"

    @pytest.mark.asyncio
    async def test_input_does_not_call_search_and_play_when_empty(self, monkeypatch):
        monkeypatch.setattr(
            SpotifyClient,
            "search_spotify_suggestions",
            lambda _: [],
        )

        mock_function = MagicMock(return_value="mocked_value")
        monkeypatch.setattr(
            SpotifyClient,
            "search_artist_and_play",
            mock_function,
        )

        app = SearchApp()
        async with app.run_test() as pilot:
            await pilot.click("#search")
            await pilot.press("enter")

            mock_function.assert_not_called()

    @pytest.mark.asyncio
    async def test_input_does_call_search_and_play_when_has_value(self, monkeypatch):
        monkeypatch.setattr(
            SpotifyClient,
            "search_spotify_suggestions",
            lambda _: [],
        )

        mock_function = MagicMock(return_value="mocked_value")
        monkeypatch.setattr(
            SpotifyClient,
            "search_artist_and_play",
            mock_function,
        )

        app = SearchApp()
        async with app.run_test() as pilot:
            app.screen.query_one("#search", Input).value = "test"
            await pilot.click("#search")
            await pilot.press("enter")

            mock_function.assert_called_once_with(artist_query="test")
