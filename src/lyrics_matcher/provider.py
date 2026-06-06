"""Lyrics providers with multi-threaded search support."""

import re
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from abc import ABC, abstractmethod

import requests


class LyricsFormat(Enum):
    """Lyrics format types."""
    PLAIN = "plain"
    SYNCED = "synced"
    ENHANCED = "enhanced"


@dataclass
class LyricTrack:
    """Lyrics track data."""
    id: str
    name: str
    track_name: str
    artist_name: str
    album_name: str
    duration: float
    instrumental: bool
    source: str = "unknown"
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None
    enhanced_lyrics: Optional[str] = None
    translation: Optional[str] = None
    romaji: Optional[str] = None


@dataclass
class WordTiming:
    """Word-level timing for enhanced lyrics."""
    word: str
    start: float
    end: float


class LyricsProvider(ABC):
    """Abstract base class for lyrics providers."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.name = "Unknown"

    @abstractmethod
    def search(self, title: str, artist: str = "", duration: float = 0.0) -> list[LyricTrack]:
        """Search for lyrics by track info."""
        pass

    def _make_request(self, url: str, params: dict = None, headers: dict = None) -> Optional[dict]:
        """Make HTTP request with error handling."""
        try:
            default_headers = {"User-Agent": "LyricsMatcher/0.2.0"}
            if headers:
                default_headers.update(headers)
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
                headers=default_headers,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None


class LrclibProvider(LyricsProvider):
    """LRC lyrics provider using lrclib.net API."""

    def __init__(self, timeout: int = 10):
        super().__init__(timeout)
        self.name = "LRCLIB"
        self.api_base = "https://lrclib.net/api"

    def search(self, title: str, artist: str = "", duration: float = 0.0) -> list[LyricTrack]:
        """Search for lyrics by track info."""
        params = {"artist_name": artist, "track_name": title}
        if duration > 0:
            params["duration"] = str(round(duration))

        data = self._make_request(f"{self.api_base}/search", params)
        if not data:
            return []

        tracks = []
        for item in data:
            tracks.append(LyricTrack(
                id=f"lrclib_{item.get('id', 0)}",
                name=item.get("name", ""),
                track_name=item.get("trackName", ""),
                artist_name=item.get("artistName", ""),
                album_name=item.get("albumName", ""),
                duration=item.get("duration", 0.0),
                instrumental=item.get("instrumental", False),
                source="LRCLIB",
                plain_lyrics=item.get("plainLyrics"),
                synced_lyrics=item.get("syncedLyrics"),
                enhanced_lyrics=item.get("syncedLyrics"),
            ))
        return tracks


class NeteaseProvider(LyricsProvider):
    """Netease Cloud Music lyrics provider."""

    def __init__(self, timeout: int = 10):
        super().__init__(timeout)
        self.name = "Netease"
        self.api_base = "https://music.163.com/api/search/get"
        self.lyrics_api = "https://music.163.com/api/song/lyric"

    def search(self, title: str, artist: str = "", duration: float = 0.0) -> list[LyricTrack]:
        """Search for lyrics via Netease API."""
        search_query = f"{artist} {title}" if artist else title
        params = {
            "s": search_query,
            "type": 1,
            "limit": 10,
        }

        data = self._make_request(self.api_base, params)
        if not data or data.get("code") != 200:
            return []

        tracks = []
        for song in data.get("result", {}).get("songs", [])[:5]:
            song_id = song.get("id")
            if not song_id:
                continue

            lyrics_data = self._get_lyrics(song_id)
            if lyrics_data:
                tracks.append(LyricTrack(
                    id=f"netease_{song_id}",
                    name=song.get("name", ""),
                    track_name=song.get("name", ""),
                    artist_name=self._join_artists(song.get("artists", [])),
                    album_name=song.get("album", {}).get("name", ""),
                    duration=song.get("duration", 0) / 1000,
                    instrumental=False,
                    source="Netease",
                    synced_lyrics=lyrics_data.get("lyric"),
                    translation=lyrics_data.get("tlyric"),
                ))
        return tracks

    def _get_lyrics(self, song_id: int) -> Optional[dict]:
        """Get lyrics for a specific song."""
        params = {"id": song_id, "lv": 1, "kv": 1, "tv": -1}
        data = self._make_request(self.lyrics_api, params)
        if data and data.get("code") == 200:
            return {
                "lyric": data.get("lrc", {}).get("lyric"),
                "tlyric": data.get("tlyric", {}).get("lyric"),
            }
        return None

    def _join_artists(self, artists: list) -> str:
        return ", ".join(a.get("name", "") for a in artists)


class QQMusicProvider(LyricsProvider):
    """QQ Music lyrics provider."""

    def __init__(self, timeout: int = 10):
        super().__init__(timeout)
        self.name = "QQ Music"
        self.search_api = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
        self.lyrics_api = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"

    def search(self, title: str, artist: str = "", duration: float = 0.0) -> list[LyricTrack]:
        """Search for lyrics via QQ Music API."""
        search_query = f"{artist} {title}" if artist else title
        params = {
            "w": search_query,
            "format": "json",
            "p": 1,
            "n": 5,
        }

        data = self._make_request(self.search_api, params)
        if not data:
            return []

        tracks = []
        song_list = data.get("data", {}).get("song", {}).get("list", [])
        for song in song_list[:5]:
            songmid = song.get("songmid")
            if not songmid:
                continue

            lyrics = self._get_lyrics(songmid)
            if lyrics:
                singer_name = ""
                singers = song.get("singer", [])
                if singers:
                    singer_name = singers[0].get("name", "")
                tracks.append(LyricTrack(
                    id=f"qqmusic_{songmid}",
                    name=song.get("songname", ""),
                    track_name=song.get("songname", ""),
                    artist_name=singer_name,
                    album_name="",
                    duration=song.get("interval", 0),
                    instrumental=False,
                    source="QQ Music",
                    synced_lyrics=lyrics,
                ))
        return tracks

    def _get_lyrics(self, songmid: str) -> Optional[str]:
        """Get lyrics for a specific song."""
        headers = {
            "Referer": "https://y.qq.com",
        }
        params = {
            "songmid": songmid,
            "format": "json",
            "nobase64": 1,
        }
        try:
            response = requests.get(
                self.lyrics_api,
                params=params,
                headers={**{"User-Agent": "LyricsMatcher/0.2.0"}, **headers},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("retcode") == 0:
                    encoded = data.get("lyric", "")
                    if encoded:
                        return base64.b64decode(encoded).decode("utf-8")
        except Exception:
            pass
        return None


class MultiProvider:
    """Multi-provider lyrics search with threading."""

    def __init__(self, timeout: int = 10, max_workers: int = 4):
        self.timeout = timeout
        self.max_workers = max_workers
        self.providers: list[LyricsProvider] = [
            LrclibProvider(timeout),
            NeteaseProvider(timeout),
            QQMusicProvider(timeout),
        ]

    def search_all(self, title: str, artist: str = "", duration: float = 0.0) -> list[LyricTrack]:
        """Search all providers concurrently."""
        all_tracks: list[LyricTrack] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(provider.search, title, artist, duration): provider
                for provider in self.providers
            }

            for future in as_completed(futures):
                try:
                    tracks = future.result()
                    all_tracks.extend(tracks)
                except Exception:
                    pass

        source_order = {"LRCLIB": 0, "Netease": 1, "QQ Music": 2}
        all_tracks.sort(key=lambda t: source_order.get(t.source, 99))
        return all_tracks

    def search_best_match(self, title: str, artist: str = "", duration: float = 0.0) -> Optional[LyricTrack]:
        """Search and return the best matching track."""
        tracks = self.search_all(title, artist, duration)
        if not tracks:
            return None

        for track in tracks:
            if track.enhanced_lyrics or track.synced_lyrics:
                return track
        return tracks[0] if tracks else None


def parse_lrc_timestamp(line: str) -> Optional[float]:
    """Parse LRC timestamp to seconds."""
    pattern = r"\[(\d{2}):(\d{2})(?:\.(\d+))?\]"
    match = re.search(pattern, line)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        ms_str = match.group(3) or "0"
        ms_str = ms_str.ljust(3, '0')[:3]
        ms = int(ms_str)
        return minutes * 60 + seconds + ms / 1000
    return None


def format_lrc_timestamp(seconds: float) -> str:
    """Format seconds to LRC timestamp."""
    total_ms = round(seconds * 1000)
    minutes = total_ms // 60000
    secs = (total_ms % 60000) // 1000
    ms = (total_ms % 60000) % 1000
    if ms % 10 == 0:
        return f"[{minutes:02d}:{secs:02d}.{ms // 10:02d}]"
    return f"[{minutes:02d}:{secs:02d}.{ms:02d}]"


def parse_enhanced_lrc(lrc: str) -> list[WordTiming]:
    """Parse enhanced LRC with word timings."""
    words: list[WordTiming] = []
    current_time = 0.0

    for line in lrc.split("\n"):
        timestamp_match = re.match(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)", line)
        if timestamp_match:
            minutes = int(timestamp_match.group(1))
            seconds = int(timestamp_match.group(2))
            ms = int(timestamp_match.group(3))
            if len(str(ms)) == 2:
                ms *= 10
            current_time = minutes * 60 + seconds + ms / 1000
            text = timestamp_match.group(4)

            word_pattern = r"<(\d{2}):(\d{2})\.(\d{2,3})>([^<\[]+)"
            for wm in re.finditer(word_pattern, text):
                w_min = int(wm.group(1))
                w_sec = int(wm.group(2))
                w_ms = int(wm.group(3))
                if len(str(w_ms)) == 2:
                    w_ms *= 10
                start = w_min * 60 + w_sec + w_ms / 1000
                word = wm.group(4).strip()
                if word:
                    words.append(WordTiming(word=word, start=start, end=current_time + 0.5))
        elif line.strip() and current_time > 0:
            text = re.sub(r"\[.*?\]", "", line).strip()
            if text:
                for char in text:
                    words.append(WordTiming(word=char, start=current_time, end=current_time + 0.3))
                current_time += 0.5

    return words


def convert_to_enhanced_lrc(synced_lrc: str, duration: float = 0.0) -> str:
    """Convert synced LRC to enhanced format with word-level timestamps."""
    if not synced_lrc:
        return synced_lrc

    words = parse_enhanced_lrc(synced_lrc)
    if not words:
        return synced_lrc

    lines = []
    current_line_time = 0.0
    current_line_words = []
    char_duration = duration / max(len(synced_lrc), 1) if duration > 0 else 0.3

    for word_timing in words:
        if not current_line_time:
            current_line_time = word_timing.start

        if word_timing.start > current_line_time + 2.0 and current_line_words:
            lines.append((current_line_time, "".join(current_line_words)))
            current_line_words = []
            current_line_time = word_timing.start

        current_line_words.append(word_timing.word)

    if current_line_words:
        lines.append((current_line_time, "".join(current_line_words)))

    result_lines = []
    for start_time, text in lines:
        result_lines.append(f"{format_lrc_timestamp(start_time)}{text}")

    return "\n".join(result_lines)


def format_enhanced_timestamp(seconds: float) -> str:
    """Format seconds to enhanced LRC timestamp format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 100)
    return f"<{minutes:02d}:{secs:02d}.{ms:02d}>"