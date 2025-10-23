from spotify_cli.app.widgets.active_device import ActiveDevice


class TestActiveDevice:
    def test_renders_string_when_no_devices(self):
        assert ActiveDevice(None).render() == "No Active device"

    def test_renders_device_string(self):
        assert ActiveDevice("Test Device").render() == "Active Device: Test Device"
