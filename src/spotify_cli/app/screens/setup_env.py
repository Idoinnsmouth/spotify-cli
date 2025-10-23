from textual import on
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input, Static, Label, Link, Button

from spotify_cli.config import save_config
from spotify_cli.spotify_service import is_spotify_config_valid


class SetupEnv(Screen):
    AUTO_FOCUS = ""
    client_id = Input(id="client_id")
    client_secret = Input(id="client_secret")
    client_creds_error = Static("Client id and secret are not valid, please re-check them and try again",
                                id="cred_error", classes="invisible")

    def compose(self):
        with Vertical():
            yield Static("Spotify Client Configuration", classes="header")
            yield Static(
                "To use this app you need to configure an app via the instructions in link below, "
                "then write the Client ID and Client Secret here"
                , classes="span")
            yield Link("https://developer.spotify.com/documentation/web-api/concepts/apps")

            with Container():
                yield Label("Client id")
                yield self.client_id
                yield Label("Client secret")
                yield self.client_secret

                yield self.client_creds_error

            yield Button("Create configuration", variant="primary", disabled=True, id="submit_config")

        yield Footer()

    @on(Input.Changed)
    def validate_inputs(self, _event: Input.Changed):
        button = self.query_one("#submit_config", Button)
        button.disabled = not all(len(_input.value) >= 2 for _input in (self.client_id, self.client_secret))

    @on(Button.Pressed)
    def submit(self, _event: Button.Pressed) -> None:
        self.client_creds_error.classes = "invisible"

        is_valid = is_spotify_config_valid(
            client_id=self.client_id.value,
            client_secret=self.client_secret.value,
        )

        if is_valid:
            save_config(
                self.client_id.value,
                client_secret=self.client_secret.value,
            )
            self.dismiss({"status": "ok"})
        else:
            self.client_creds_error.classes = ""
