from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from spotify_cli.schemas.track import Track


class TrackDetail(Widget):
    track: reactive[Track] = reactive(None, recompose=True)

    def __init__(self, *children: Widget, track: Track | None = None):
        super().__init__(*children)
        self.track = track

    def compose(self):
        if not self.track:
            yield Static("No track selected")
            return

        yield Container(
        Static(f"Track: {self.track.name}"),
            Static(f"Album: {self.track.album}"),
            Static(f"Artist: {self.track.artist}"),
            id="track_text_details"
        )
