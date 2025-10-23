import pytest
from textual.app import App, ComposeResult
from textual.widgets import Static

from spotify_cli.app.widgets.track_details import TrackDetail
from spotify_cli.schemas.track import Track
from spotify_cli.tests.utils import generate_test_track_instance


class TrackDetailApp(App):
    def __init__(self, track: Track | None):
        super().__init__()
        self.track = track

    def compose(self) -> ComposeResult:
        yield TrackDetail(track=self.track)


class TestTrackDetails:
    @pytest.mark.asyncio
    async def test_no_track(self):
        app = TrackDetailApp(None)

        async with app.run_test():
            static = app.query_one(Static)
            assert static.content == "No track selected"

    @pytest.mark.asyncio
    async def test_shows_track_text_details(self):
        track = generate_test_track_instance()
        app = TrackDetailApp(track)

        async with app.run_test():
            track_text_details_container = app.query_one("#track_text_details")
            track_details_statics = track_text_details_container.query_children(Static)
            assert track_details_statics[0].content == f"Track: {track.name}"
            assert track_details_statics[1].content == f"Album: {track.album.name}"
            assert track_details_statics[2].content == f"Artist: {track.artist}"
