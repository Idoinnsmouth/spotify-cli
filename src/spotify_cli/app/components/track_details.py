from math import floor

from rich.text import Text
from textual.containers import Container, Horizontal, Grid
from textual.reactive import reactive
from textual.widget import Widget, AwaitMount
from textual.widgets import Static

from spotify_cli.schemas.track import Track
from spotify_cli.utils.ascii_image_converter import get_ascii_of_image


class TrackDetail(Widget):
    track: reactive[Track] = reactive(None, recompose=True)
    album_image: reactive[str] = reactive(None, recompose=True)

    def __init__(self, *children: Widget, track: Track | None = None):
        super().__init__(*children)
        self.track = track

    def compose(self):
        # if not self.track:
        #     yield Static("No track selected")
        #     return
        #
        # yield Horizontal(
        #     Container(
        #         Static(f"Track: {self.track.name}"),
        #             Static(f"Album: {self.track.album.name}"),
        #             Static(f"Artist: {self.track.artist}"),
        #         id="track_text_details"
        #     ),
        #     Container(
        #         Static(Text(self.album_image, no_wrap=True)),
        #         id="album_cover"
        #     ),
        #     id="track_layout"
        # )

        yield Horizontal(
            Container(
                Static(f"Track: Devil Trigger"),
                    Static(f"Album: DMC"),
                    Static(f"Artist: DMC"),
                id="track_text_details"
            ),
            Container(
                Container(
                    Static(Text((self.album_image or "a"), no_wrap=True)),
                ),
                id="album_cover"
            ),
            id="track_layout"
        )

    async def on_mount(self):
        if self.track:
            self._start_service_call(self.track)


    def watch_track(self, old: "Track | None", new: "Track | None"):
        # if new is None or (old and old.name == new.name):
        #     return
        self._start_service_call(new)


    def _start_service_call(self, track: "Track"):
        """Start/replace a background job for the current track."""
        # Cancel/replace any in-flight job for previous tracks
        self.run_worker(
            self._fetch_track_album_image(track),
            exclusive=True,
            group="track-service",
            thread=False,
            # name=f"track-service:{track.id if hasattr(track, 'id') else track.name}",
        )

    async def _fetch_track_album_image(self, track: "Track"):
        # album_image = track.album.get_album_image()
        # self.album_image = get_ascii_of_image(album_image.url, floor(((80 / self.container_viewport.width) * 100)))
        w, vh = self.app.size
        self.album_image = get_ascii_of_image(
            "https://i.scdn.co/image/ab67616d0000b2736ab9aff73fa181d27dd8b9e0",
            height=64,
            width_ratio=0.1
        )


