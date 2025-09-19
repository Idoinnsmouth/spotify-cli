from spotipy import SpotifyOAuth

from spotify_cli.config import Config


def get_spotify_client(cfg: Config):
    auth = SpotifyOAuth(
        client_id=cfg.client_id,
        client_secret=cfg.client_secret,
        redirect_uri=cfg.redirect_uri,
        scope=cfg.scopes,
        cache_path=cfg.cache_path,
        open_browser=True,
    )
    import spotipy
    return spotipy.Spotify(auth_manager=auth)