from math import floor

from rich.text import Text
from textual.containers import Container, Horizontal, Grid, Vertical
from textual.reactive import reactive
from textual.widget import Widget, AwaitMount
from textual.widgets import Static

from spotify_cli.schemas.track import Track
from spotify_cli.utils.pixelate_images import get_image_from_url


class TrackDetail(Widget):
    track: reactive[Track] = reactive(None, recompose=True)
    album_image: reactive[str] = reactive(None, recompose=True)
    pixel_view = Static()

    def __init__(self, *children: Widget, track: Track | None = None):
        super().__init__(*children)
        self.track = track

    def compose(self):
        if not self.track:
            yield Static("No track selected")
            return

        yield Vertical(
            Container(
                Static(f"Track: {self.track.name}"),
                Static(f"Album: {self.track.album.name}"),
                Static(f"Artist: {self.track.artist}"),
                id="track_text_details"
            ),
            Container(
                self.pixel_view,
                id="album_cover"
            ),
            id="track_layout"
        )

    async def on_mount(self):
        if self.track:
            self._start_service_call(self.track)

    def watch_track(self, old: "Track | None", new: "Track | None"):
        if new is None or (old and old.name == new.name):
            return
        self._start_service_call(new)

    def _start_service_call(self, track: "Track"):
        """Start/replace a background job for the current track."""
        # Cancel/replace any in-flight job for previous tracks
        self.run_worker(
            self._fetch_track_album_image(track),
            exclusive=True,
            group="track-service",
            thread=False,
            name=f"track-service:{track.name}",
        )

    async def _fetch_track_album_image(self, track: "Track"):
        if self.pixel_view is None:
            return

        album_image = track.album.get_album_image()
        if album_image is None:
            return

        # todo - maybe do the size dynmicly to the terminal size
        img = get_image_from_url(
            album_image.url,
            (23, 23)
        )
        self.pixel_view.update(img)
