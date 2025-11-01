from typing import Any, Optional, Callable

from textual.message import Message
from textual.screen import Screen


class ScreenChange(Message):
    def __init__(self, screen: type[Screen], params: dict[str, Any], callback: Optional[Callable]):
        self.screen = screen
        self.params = params
        self.callback = callback
        super().__init__()
