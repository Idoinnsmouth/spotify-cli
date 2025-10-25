import pytest
import spotipy
from spotipy import Spotify
from textual.app import App, ComposeResult
from textual.widgets import Static, RadioSet, RadioButton

from spotify_cli.app.screens.choose_device import ChooseDevice
from spotify_cli.schemas.device import Device
from spotify_cli.tests.utils import MockSpotify, generate_test_device

spotipy.Spotify = MockSpotify


class ChooseDeviceApp(App):
    def __init__(self, device: Device = None):
        super().__init__()
        self.device = device

    def compose(self) -> ComposeResult:
        yield ChooseDevice(
            sp=Spotify(),
            active_device=self.device
        )


class TestChooseDevice:
    @pytest.mark.asyncio
    async def test_no_devices(self, monkeypatch):
        monkeypatch.setattr(
            "spotify_cli.app.screens.choose_device.get_devices",
            lambda sp: [],
        )

        app = ChooseDeviceApp()

        async with app.run_test():
            static = app.query_one(Static)
            assert static.content == "No available devices"

    @pytest.mark.asyncio
    async def test_list_devices_and_no_active(self, monkeypatch):
        devices = [generate_test_device(name="device1"), generate_test_device(name="device2")]
        monkeypatch.setattr(
            "spotify_cli.app.screens.choose_device.get_devices",
            lambda sp: devices
        )

        app = ChooseDeviceApp()

        async with app.run_test():
            radio_choices = app.query(RadioButton)

            assert len(radio_choices) == 2
            assert radio_choices[0].label == devices[0].name
            assert radio_choices[0].id == "device-" + devices[0].id
            assert radio_choices[0].value == False

            assert radio_choices[1].label == devices[1].name
            assert radio_choices[1].id == "device-" + devices[1].id
            assert radio_choices[1].value == False

    @pytest.mark.asyncio
    async def test_shows_active_device(self, monkeypatch):
        devices = [generate_test_device(name="device1"), generate_test_device(name="device2")]
        monkeypatch.setattr(
            "spotify_cli.app.screens.choose_device.get_devices",
            lambda sp: devices
        )

        app = ChooseDeviceApp(device=devices[0])

        async with app.run_test():
            radio_choices = app.query(RadioButton)
            assert radio_choices[0].value == True