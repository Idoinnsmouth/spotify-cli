from typing import Optional

from spotipy import SpotifyOauthError
from textual import on
from textual.app import App
from spotify_cli.app.screens.main import Main, ScreenChange
from spotify_cli.app.screens.setup_env import SetupEnv
from spotify_cli.core.config import Config
from spotify_cli.core.spotify import SpotifyClient


class SpotifyApp(App):
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False
    TITLE = "Spotify TUI"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    show_config_setup = False
    service: SpotifyClient

    def __init__(self):
        super().__init__()
        self._debug_mode = True
        try:
            cfg = Config()
            self.service = SpotifyClient.from_config(cfg)
            self.show_config_setup = False
        except SpotifyOauthError:
            self.show_config_setup = True

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        if self.show_config_setup:
            self.push_screen(SetupEnv(), self.on_setup_finished)
        else:
            self.push_screen(Main())

    def on_setup_finished(self, new_cfg: Config) -> None:
        self.service = SpotifyClient.from_config(new_cfg)
        self.push_screen(Main())

    def action_quit(self):
        self.exit()

    @on(ScreenChange)
    def handle_screen_change(self, message: ScreenChange):
        self.push_screen(
            message.screen(
                **message.params,
            ),
            message.callback
        )
