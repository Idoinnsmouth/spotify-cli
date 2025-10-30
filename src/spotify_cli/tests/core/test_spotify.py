from unittest.mock import MagicMock

import pytest

from spotify_cli.core.spotify import SpotifyClient, SearchElementTypes, NoActiveDeviceFound
from spotify_cli.schemas.device import Device
from spotify_cli.tests.utils import MockSpotify, MockPlatformAdapter, generate_test_device, generate_test_playback_state


class TestSpotify:
    def test_get_devices_return_empty_list_when_no_devices(self):
        mock_spotify = MockSpotify()
        mock_spotify.devices = lambda: {"devices": []}
        sp_client = SpotifyClient(sp=mock_spotify)
        devices = sp_client.get_devices()

        assert devices == []

    def test_get_devices_return_list_of_device_instances(self):
        devices = {
            "devices": [
                {
                    "id": "device_001",
                    "is_active": False,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "Kitchen speaker",
                    "type": "computer",
                    "volume_percent": 59,
                    "supports_volume": False
                },
                {
                    "id": "device_002",
                    "is_active": True,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "Living room TV",
                    "type": "smart_tv",
                    "volume_percent": 82,
                    "supports_volume": True
                }
            ]
        }

        mock_spotify = MockSpotify()
        mock_spotify.devices = lambda: devices
        sp_client = SpotifyClient(sp=mock_spotify)
        devices = sp_client.get_devices()

        assert len(devices) == 2
        assert devices[0].id == "device_001"
        assert devices[1].id == "device_002"

    def test_get_first_active_device_with_multiple_devices(self):
        devices = {
            "devices": [
                {
                    "id": "device_001",
                    "is_active": False,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "Kitchen speaker",
                    "type": "computer",
                    "volume_percent": 59,
                    "supports_volume": False
                },
                {
                    "id": "device_002",
                    "is_active": True,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "Living room TV",
                    "type": "smart_tv",
                    "volume_percent": 82,
                    "supports_volume": True
                }
            ]
        }

        mock_spotify = MockSpotify()
        mock_spotify.devices = lambda: devices
        sp_client = SpotifyClient(sp=mock_spotify)
        device = sp_client.get_first_active_device()

        assert device.id == "device_002"

    def test_get_first_active_device_return_none_when_no_active_device(self):
        devices = {
            "devices": [
                {
                    "id": "device_001",
                    "is_active": False,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "Kitchen speaker",
                    "type": "computer",
                    "volume_percent": 59,
                    "supports_volume": False
                },
                {
                    "id": "device_002",
                    "is_active": False,
                    "is_private_session": False,
                    "is_restricted": False,
                    "name": "Living room TV",
                    "type": "smart_tv",
                    "volume_percent": 82,
                    "supports_volume": True
                }
            ]
        }

        mock_spotify = MockSpotify()
        mock_spotify.devices = lambda: devices
        sp_client = SpotifyClient(sp=mock_spotify)
        device = sp_client.get_first_active_device()

        assert device is None

    def test_get_first_active_device_return_none_when_no_devices(self):
        devices = {
            "devices": []
        }

        mock_spotify = MockSpotify()
        mock_spotify.devices = lambda: devices
        sp_client = SpotifyClient(sp=mock_spotify)
        device = sp_client.get_first_active_device()

        assert device is None

    @pytest.mark.asyncio
    async def test_wait_for_devices_return_active_device_after_retries(self):
        counter = 10
        failure_amount = 0

        def mock_get_first_active_device():
            nonlocal failure_amount
            if failure_amount < counter:
                failure_amount += 1
                return None
            else:
                return Device(
                    id="device_0001",
                    is_active=True,
                    is_private_session=False,
                    is_restricted=False,
                    name="test device",
                    type="device",
                    volume_percent=0,
                    supports_volume=True,
                )

        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.get_first_active_device = mock_get_first_active_device
        device = await sp_client.wait_for_device(delay=0)

        assert device.id == "device_0001"

    @pytest.mark.asyncio
    async def test_wait_for_devices_return_none_after_retries(self):
        def mock_get_first_active_device():
            return None

        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.get_first_active_device = mock_get_first_active_device
        device = await sp_client.wait_for_device(tries=2, delay=0)

        assert device is None

    def test_search_spotify_tracks_calls_search_with_params(self):
        search_res = {
            "tracks": {
                "href": "https://api.spotify.com/v1/me/shows?offset=0&limit=20",
                "limit": 20,
                "next": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "offset": 0,
                "previous": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "total": 4,
                "items": []
            }
        }
        mock_spotify = MockSpotify()
        mock_spotify.search = MagicMock(return_value=search_res)
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.search_spotify_tracks("test", search_element=SearchElementTypes.TRACK, limit=1)

        mock_spotify.search.assert_called_once_with(q=f"track:test", type="track", limit=1)

    def test_search_spotify_album_calls_search_with_params(self):
        search_res = {
            "tracks": {
                "href": "https://api.spotify.com/v1/me/shows?offset=0&limit=20",
                "limit": 20,
                "next": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "offset": 0,
                "previous": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "total": 4,
                "items": []
            }
        }
        mock_spotify = MockSpotify()
        mock_spotify.search = MagicMock(return_value=search_res)
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.search_spotify_tracks("test", search_element=SearchElementTypes.ALBUM, limit=1)

        mock_spotify.search.assert_called_once_with(q=f"album:test", type="album", limit=1)

    def test_search_spotify_artist_calls_search_with_params(self):
        search_res = {
            "tracks": {
                "href": "https://api.spotify.com/v1/me/shows?offset=0&limit=20",
                "limit": 20,
                "next": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "offset": 0,
                "previous": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "total": 4,
                "items": []
            }
        }
        mock_spotify = MockSpotify()
        mock_spotify.search = MagicMock(return_value=search_res)
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.search_spotify_tracks("test", search_element=SearchElementTypes.ARTIST, limit=10)

        mock_spotify.search.assert_called_once_with(q=f"artist:test", type="track", limit=10)

    def test_search_spotify_suggestions_calls_search_with_params(self):
        search_res = {
            "tracks": {
                "href": "https://api.spotify.com/v1/me/shows?offset=0&limit=20",
                "limit": 20,
                "next": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "offset": 0,
                "previous": "https://api.spotify.com/v1/me/shows?offset=1&limit=1",
                "total": 4,
                "items": []
            }
        }
        mock_spotify = MockSpotify()
        mock_spotify.search = MagicMock(return_value=search_res)
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.search_spotify_suggestions("test", search_element=SearchElementTypes.ARTIST, limit=10)
        mock_spotify.search.assert_called_once_with(q=f"artist:test", type="artist", limit=10)

    @pytest.mark.asyncio
    async def test_play_by_uris_or_context_uri_raise_when_no_device_found(self):
        mock_spotify = MockSpotify()
        mock_platform_adapter = MockPlatformAdapter()
        mock_platform_adapter.ensure_spotify_running = lambda: ""
        mock_spotify.devices = lambda: {"devices": []}
        sp_client = SpotifyClient(sp=mock_spotify, platform=mock_platform_adapter)

        with pytest.raises(NoActiveDeviceFound):
            await sp_client.play_by_uris_or_context_uri(context_uri="test-uri")

    @pytest.mark.asyncio
    async def test_play_by_uris_or_context_uri_raise_when_no_uris_or_context_uri(self):
        mock_spotify = MockSpotify()
        mock_platform_adapter = MockPlatformAdapter()
        mock_platform_adapter.ensure_spotify_running = lambda: ""
        mock_spotify.devices = lambda: {"devices": []}
        sp_client = SpotifyClient(sp=mock_spotify, platform=mock_platform_adapter)

        with pytest.raises(ValueError):
            await sp_client.play_by_uris_or_context_uri()

    def test_play_or_pause_track_raise_when_no_active_device_found(self):
        mock_spotify = MockSpotify()
        mock_platform_adapter = MockPlatformAdapter()
        mock_platform_adapter.ensure_spotify_running = lambda: ""
        mock_spotify.devices = lambda: {"devices": []}
        sp_client = SpotifyClient(sp=mock_spotify, platform=mock_platform_adapter)

        with pytest.raises(NoActiveDeviceFound):
            sp_client.play_or_pause_track(active_device=None)

    def test_play_or_pause_track_pause_when_track_is_playing(self):
        device = generate_test_device()
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.get_playback_state = lambda: generate_test_playback_state(is_playing=True, device_id=device.id)
        mock_spotify.pause_playback = MagicMock()

        sp_client.play_or_pause_track(active_device=device)

        mock_spotify.pause_playback.assert_called_once_with(device_id=device.id)

    def test_play_or_pause_track_resume_on_same_device(self):
        device = generate_test_device()
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.get_playback_state = lambda: generate_test_playback_state(is_playing=False, device_id=device.id)
        mock_spotify.start_playback = MagicMock()

        sp_client.play_or_pause_track(active_device=device)

        mock_spotify.start_playback.assert_called_once_with(device_id=device.id)

    def test_play_or_pause_track_transfer_and_resume_on_diffrent_device(self):
        device = generate_test_device()
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)
        sp_client.get_playback_state = lambda: generate_test_playback_state(is_playing=False,
                                                                            device_id="another_device")
        mock_spotify.transfer_playback = MagicMock()

        sp_client.play_or_pause_track(active_device=device)

        mock_spotify.transfer_playback.assert_called_once_with(device_id=device.id)

    def test__can_start_playback_return_false_when_no_playback(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        playback_state = None

        assert sp_client._can_start_playback(playback_state) == False

    def test__can_start_playback_return_false_when_playback_is_playing(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        playback_state = generate_test_playback_state(
            is_playing=True,
        )

        assert sp_client._can_start_playback(playback_state) == False

    def test__can_start_playback_return_false_when_playback_disallows_resuming(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        playback_state = generate_test_playback_state(
            is_playing=False,
            is_resumable=False
        )

        assert sp_client._can_start_playback(playback_state) == False

    def test__can_start_playback_return_true_when_playback_is_paused_and_allowed_resuming(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        playback_state = generate_test_playback_state(
            is_playing=False
        )

        assert sp_client._can_start_playback(playback_state) == True

    def test__can_pause_playback_return_false_when_no_playback(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        assert sp_client._can_pause_playback(None) == False

    def test__can_pause_playback_return_false_playback_disallows_pausing(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        playback_state = generate_test_playback_state(
            is_playing=True,
            is_pausable=False
        )

        assert sp_client._can_pause_playback(playback_state) == False

    def test__can_pause_playback_return_true_when_allowed_to_pause(self):
        mock_spotify = MockSpotify()
        sp_client = SpotifyClient(sp=mock_spotify)

        playback_state = generate_test_playback_state(
            is_playing=True,
        )

        assert sp_client._can_pause_playback(playback_state) == True