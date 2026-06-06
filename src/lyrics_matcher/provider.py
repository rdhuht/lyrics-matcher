"""LRC lyrics provider using Lrclib API."""

import re
from dataclasses import dataclass
from typing import Optional

import requests

Lrclib_API = "https://lrclib.net/api"


@dataclass
class LyricTrack:
    """Lyrics track data."""

    id: int
    name: str
    track_name: str
    artist_name: str
    album_name: str
    duration: float
    instrumental: bool
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None


class LrclibProvider:
    """LRC lyrics provider using lrclib.net API."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def search(self, title: str, artist: str = "", duration: float = 0.0) -> list[LyricTrack]:
        """Search for lyrics by track info."""
        params = {"artist_name": artist, "track_name": title}
        if duration > 0:
            params["duration"] = str(round(duration))

        try:
            response = requests.get(
                f"{Lrclib_API}/search",
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "LyricsMatcher/0.1.0"},
            )
            response.raise_for_status()
            results = response.json()

            tracks = []
            for item in results:
                tracks.append(
                    LyricTrack(
                        id=item.get("id", 0),
                        name=item.get("name", ""),
                        track_name=item.get("trackName", ""),
                        artist_name=item.get("artistName", ""),
                        album_name=item.get("albumName", ""),
                        duration=item.get("duration", 0.0),
                        instrumental=item.get("instrumental", False),
                        plain_lyrics=item.get("plainLyrics"),
                        synced_lyrics=item.get("syncedLyrics"),
                    )
                )
            return tracks
        except requests.RequestException:
            return []

    def get(self, track_id: int) -> Optional[LyricTrack]:
        """Get lyrics by track ID."""
        try:
            response = requests.get(
                f"{Lrclib_API}/get/{track_id}",
                timeout=self.timeout,
                headers={"User-Agent": "LyricsMatcher/0.1.0"},
            )
            response.raise_for_status()
            item = response.json()
            return LyricTrack(
                id=item.get("id", 0),
                name=item.get("name", ""),
                track_name=item.get("trackName", ""),
                artist_name=item.get("artistName", ""),
                album_name=item.get("albumName", ""),
                duration=item.get("duration", 0.0),
                instrumental=item.get("instrumental", False),
                plain_lyrics=item.get("plainLyrics"),
                synced_lyrics=item.get("syncedLyrics"),
            )
        except requests.RequestException:
            return None


def parse_lrc_timestamp(line: str) -> Optional[float]:
    """Parse LRC timestamp to seconds."""
    pattern = r"\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\]"
    match = re.search(pattern, line)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        ms = int(match.group(3) or "0")
        if len(str(ms)) == 2:
            ms *= 10
        return minutes * 60 + seconds + ms / 1000
    return None


def format_lrc_timestamp(seconds: float) -> str:
    """Format seconds to LRC timestamp."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 100)
    return f"[{minutes:02d}:{secs:02d}.{ms:02d}]"