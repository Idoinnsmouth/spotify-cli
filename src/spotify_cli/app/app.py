from textual import on
from textual.app import App
from spotify_cli.app.screens.main import Main, ScreenChange
from spotify_cli.app.screens.search import SearchScreen
from spotify_cli.app.screens.setup_env import SetupEnv
from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config, ConfigValuesError


class SpotifyApp(App):
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False
    TITLE = "Spotify TUI"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    show_config_setup = False

    def __init__(self):
        super().__init__()
        self._debug_mode = True
        self._load_config()

    def _load_config(self):
        try:
            config = Config()
            config.load_config()
            self.sp = get_spotify_client(config)
            self.show_config_setup = False
        except ConfigValuesError:
            self.show_config_setup = True

    def on_mount(self) -> None:
        self.theme = "tokyo-night"

        def _handle_setup_env_callback(_):
            self._load_config()
            self.push_screen(Main())

        if self.show_config_setup:
            self.push_screen(SetupEnv(), _handle_setup_env_callback)
        else:
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
