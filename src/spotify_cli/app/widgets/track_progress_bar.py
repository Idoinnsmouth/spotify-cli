from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import ProgressBar

from spotify_cli.schemas.playback import PlaybackState


class TrackProgressBar(Widget):
    playback_state: reactive[PlaybackState | None] = reactive(None)

    def compose(self):
        yield ProgressBar(show_percentage=False, show_eta=True)

    def on_mount(self):
        self.query_one(ProgressBar).update(total=0)
        # self.query_one(ProgressBar).update(total=self.playback_state.duration_ms, progress=self.playback_state.progress_ms)

    def watch_playback_state(self, new: PlaybackState | None, old: PlaybackState | None):
        if new:
            self.query_one(ProgressBar).update(total=new.duration_ms, progress=new.progress_ms)
