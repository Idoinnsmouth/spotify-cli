from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Placeholder, Static

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

        yield Static(self.track.name or "")
        yield Static(getattr(self.track, "album", "") or "")
        yield Static(getattr(self.track, "artist", "") or "")