import subprocess
import sys
import time

from spotipy import Spotify

from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config


def ensure_spotify_running():
    # todo - this runs spotify on current machine only
    try:
        subprocess.run(["pgrep", "-x", "Spotify"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.run(["open", "-a", "Spotify"])
        time.sleep(1.5)


def active_device(sp):
    devs = sp.devices().get("devices", [])
    for d in devs:
        if d.get("is_active"):
            return d
    return devs[0] if devs else None


def wait_for_device(sp, tries=12, delay=0.5):
    for _ in range(tries):
        d = active_device(sp)
        if d:
            return d
        time.sleep(delay)
    return None


def play_artist(sp: Spotify, artist_query, market="from_token"):
    res = sp.search(q=f"artist:{artist_query}", type="artist", limit=1)
    items = res.get("artists", {}).get("items", [])
    if not items:
        raise ValueError("Not artist found")
        # todo - handle send back message
        # print(f"No artist found for: {artist_query}")
        # sys.exit(1)

    artist = items[0]
    top = sp.artist_top_tracks(artist["id"], country=market)
    uris = [t["uri"] for t in top.get("tracks", [])][:10]
    if not uris:
        # todo - handle send back message
        pass
        # print("No playable tracks found.")
        # sys.exit(1)

    ensure_spotify_running()
    dev = wait_for_device(sp)
    if not dev:
        pass
        # todo - handle send back message
        # print("No active device. Open Spotify and try again.")
        # sys.exit(1)

    sp.start_playback(uris=uris, device_id=sp.devices().get("devices")[0].get("id"))


def play_or_pause_track(sp: Spotify):
    device_id = sp.devices().get("devices")[0].get("id")
    currently_playing = sp.currently_playing()

    if not currently_playing.get("is_playing"):
        sp.start_playback(device_id=device_id)
    else:
        sp.pause_playback(device_id=device_id)


if __name__ == "__main__":
    sp = get_spotify_client(Config())
    play_or_pause_track(sp)