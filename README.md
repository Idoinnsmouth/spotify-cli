# Spotify CLI

A terminal-based Spotify client built with Python and Textual.  
It allows you to browse, search, and control Spotify playback directly from your command line with a responsive TUI interface.

---

## Features

- View current playback status in real time  
- Search for artists, tracks, and albums  
- Play, pause, and transfer playback between devices  
- Built using Textual, Spotipy, and asyncio for responsive performance  
- Caches API data to minimize rate limits and improve speed  

---

## Tech Stack

- Python 3.11+  
- [Textual](https://github.com/Textualize/textual) – for the TUI interface  
- [Spotipy](https://github.com/plamere/spotipy) – Spotify Web API wrapper  
- AsyncIO, Rich, Requests  

---

## Setup

- Create a Spotify Developer App at https://developer.spotify.com/dashboard
- Copy your Client ID, Client Secret, and Redirect URI.  
- Add them to a .env file in the project root:
```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8080
```
---

## Installation

```bash
# Clone the repository
git clone https://github.com/Idoinnsmouth/spotify-cli.git
cd spotify-cli

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Roadmap

- User Library UI
- .env setup as part of app flow
- Implementing full playback features
- Tests
- Publish as a pip package
---
