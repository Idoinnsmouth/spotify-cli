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

- Python 3.12+  
- [Textual](https://github.com/Textualize/textual) – for the TUI interface  
- [Spotipy](https://github.com/plamere/spotipy) – Spotify Web API wrapper  
- AsyncIO, Rich, Requests  

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
pip install -e .
```

---

## Roadmap

- User Library UI
- .env setup as part of app flow
- Implementing full playback features
- Tests
- Publish as a pip package
---
