from spotipy import Spotify
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import RadioSet, RadioButton, Footer, Static

from spotify_cli.schemas.device import Device


class ChooseDevice(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Close"),
    ]

    devices: list[Device]

    def __init__(self, active_device: Device | None):
        super().__init__()
        self.active_device = active_device

    def compose(self) -> ComposeResult:
        self.devices = self.app.service.get_devices()

        if len(self.devices) > 0:
            with RadioSet(id="devices"):
                for device in self.devices:
                    yield RadioButton(
                        label=device.name,
                        id=f"device-{device.id}",
                        value=(self.active_device.id == device.id if self.active_device else device.is_active),
                    )
        else:
            yield Static("No available devices")

        yield Footer()

    def action_pop_screen(self):
        self.dismiss()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> Device | None:
        device_id = event.pressed.id.removeprefix("device-")
        new_device = next((_device for _device in self.devices if _device.id == device_id), None)
        self.dismiss(new_device)
