from textual.reactive import reactive
from textual.widget import Widget


class ActiveDevice(Widget):
    active_device_name: reactive[str | None] = reactive(default=None)

    def __init__(self, active_device_name: str | None):
        super().__init__()
        self.active_device_name = active_device_name

    def render(self) -> str:
        if self.active_device_name:
            return f"Active Device: {self.active_device_name}"
        else:
            return "No Active device"