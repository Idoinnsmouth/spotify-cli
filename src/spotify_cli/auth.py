from spotipy import SpotifyOAuth, Spotify, CacheFileHandler

from spotify_cli.config import Config
from spotify_cli.utils.caching import get_spotipy_cache_path


def get_spotify_client(cfg: Config) -> Spotify:
    auth = SpotifyOAuth(
        client_id=cfg.client_id,
        client_secret=cfg.client_secret,
        redirect_uri=cfg.redirect_uri,
        scope=cfg.scopes,
        open_browser=True,
        cache_handler=CacheFileHandler(
            cache_path=get_spotipy_cache_path()
        )
    )
    import spotipy
    return spotipy.Spotify(auth_manager=auth)