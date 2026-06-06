"""Audio file handling utilities."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis


@dataclass
class AudioMetadata:
    """Audio file metadata."""

    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: float = 0.0


SUPPORTED_FORMATS = {".mp3", ".flac", ".ogg", ".m4a", ".wav", ".opus"}


def is_supported_audio(path: Path) -> bool:
    """Check if file is a supported audio format."""
    return path.suffix.lower() in SUPPORTED_FORMATS


def get_metadata(file_path: Path) -> AudioMetadata:
    """Extract metadata from audio file."""
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return AudioMetadata()

        metadata = AudioMetadata()

        if hasattr(audio, "tags") and audio.tags:
            tags = audio.tags
            metadata.title = _get_tag_value(tags, ["TIT2", "title", "\xa9nam"])
            metadata.artist = _get_tag_value(tags, ["TPE1", "artist", "\xa9ART"])
            metadata.album = _get_tag_value(tags, ["TALB", "album", "\xa9alb"])

        metadata.duration = getattr(audio.info, "length", 0.0)

        if not metadata.title:
            metadata.title = file_path.stem

        return metadata
    except Exception:
        return AudioMetadata(title=file_path.stem)


def _get_tag_value(tags, keys: list[str]) -> Optional[str]:
    """Get tag value from various possible key names."""
    for key in keys:
        try:
            if key in tags:
                value = tags[key]
                if isinstance(value, list) and value:
                    value = value[0]
                if value:
                    return str(value)
        except Exception:
            continue
    return None


def write_lyrics_to_file(file_path: Path, lyrics: str, format: str = "lrc") -> bool:
    """Write lyrics to audio file tags."""
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return False

        if isinstance(audio, MP3):
            audio.tags = mutagen.mp3.MP3Tags()
        elif isinstance(audio, FLAC):
            pass
        elif isinstance(audio, OggVorbis):
            pass

        lyrics_key = "USLT::eng" if format == "lrc" else "SYLT::eng"
        audio[lyrics_key] = lyrics

        audio.save()
        return True
    except Exception:
        return False


def save_lyrics_to_file(audio_path: Path, lyrics: str, format: str = "lrc") -> Path:
    """Save lyrics to a separate file next to the audio file."""
    lyrics_path = audio_path.with_suffix(f".{format}")
    lyrics_path.write_text(lyrics, encoding="utf-8")
    return lyrics_path


def clean_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    return re.sub(r'[<>:"/\\|?*]', "", name)