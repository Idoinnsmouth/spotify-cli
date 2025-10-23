from spotify_cli.app.app import SpotifyApp

def spotify_tui():
    app = SpotifyApp()
    app.run()

if __name__ == "__main__":
    spotify_tui()