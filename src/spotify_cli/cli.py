import sys

import click
from spotipy import Spotify

from spotify_cli.app.app import SpotifyApp
from spotify_cli.auth import get_spotify_client
from spotify_cli.config import Config
from spotify_cli.spotify_service import play_artist

def get_client() -> Spotify:
    cfg = Config()
    if not (cfg.client_id and cfg.client_secret):
        raise Exception("Config Params are missing")

    sp = get_spotify_client(cfg)
    return sp

def search_artists(prefix: str) -> list[str]:
    sp = get_client()
    results = sp.search(q=f"artist:{prefix}", type="artist", limit=10)
    return [a["name"] for a in results["artists"]["items"]]

class ArtistArg(click.ParamType):
    name = "artist"

    def shell_complete(self, ctx, param, incomplete: str):
        # Return completion items based on the current text (incomplete)
        names = search_artists(incomplete) if incomplete else []
        from click.shell_completion import CompletionItem
        return [CompletionItem(n) for n in names]

ARTIST = ArtistArg()


@click.group()
def main():
    """Spotify terminal controller."""
    pass

# todo - switch to textual and build a tui (:
@main.command("play")
@click.argument("query", nargs=-1, required=True)
@click.option("--type", "qtype", type=click.Choice(["artist", "track", "album"]), default="artist")
# @click.argument("artist", type=ARTIST)
def play_cmd(query, qtype):
    """Play an artist/track/album by query."""
    q = "".join(query)
    sp = get_client()

    if not sp:
        click.echo("[Info] API not configured. Opening Spotify search…")
        # open_search_fallback(q)
        return

    if qtype == "artist":
        play_artist(sp, q)
    # elif qtype == "track":
    #     play_track(sp, q)
    # else:
    #     play_album(sp, q)

# @main.command("resume")
# def resume_cmd():
#     """Resume last playback."""
#     sp, cfg = _client_or_fallback()
#     if not sp:
#         click.echo("[Info] API not configured.")
#         return
#     resume(sp)

if __name__ == "__main__":
    app = SpotifyApp()
    app.run()