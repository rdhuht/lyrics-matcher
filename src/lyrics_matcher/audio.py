"""Audio file handling utilities with lyrics tag support."""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.oggspeex import OggSpeex
from mutagen.oggopus import OggOpus
from mutagen.wave import WAVE


class LyricsFormat(Enum):
    """Output lyrics format."""
    LRC = "lrc"
    ENHANCED_LRC = "lrc"
    SRT = "srt"
    ASS = "ass"


@dataclass
class AudioMetadata:
    """Audio file metadata."""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: float = 0.0


SUPPORTED_FORMATS = {".mp3", ".flac", ".ogg", ".m4a", ".wav", ".opus", ".wma", ".aac"}


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


def _get_audio_type(audio) -> str:
    """Get the audio type as string."""
    return type(audio).__name__


def write_lyrics_to_tag(file_path: Path, lyrics: str, lyrics_format: LyricsFormat = LyricsFormat.LRC) -> bool:
    """Write lyrics to audio file metadata tags.

    Supports MP3 (USLT), FLAC (LYRICS), OGG (LYRICSBASE64), M4A (----)
    """
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return False

        audio_type = _get_audio_type(audio)

        if audio_type == "MP3":
            _write_mp3_lyrics(audio, lyrics)
        elif audio_type == "FLAC":
            _write_flac_lyrics(audio, lyrics)
        elif audio_type in ("OggVorbis", "OggSpeex", "OggOpus"):
            _write_ogg_lyrics(audio, lyrics)
        elif audio_type == "MP4":
            _write_m4a_lyrics(audio, lyrics)
        elif audio_type == "WAVE":
            _write_wave_lyrics(audio, lyrics)
        else:
            return False

        audio.save()
        return True
    except Exception as e:
        return False


def _write_mp3_lyrics(audio: MP3, lyrics: str) -> None:
    """Write lyrics to MP3 file using USLT frame."""
    if audio.tags is None:
        audio.tags = mutagen.mp3.MP3Tags()
        audio.tags.add(mutagen.mp3.MP3Frame())

    from mutagen.id3 import USLT, Encoding
    audio.tags["USLT::eng"] = USLT(
        encoding=Encoding.UTF8,
        lang="eng",
        desc="",
        text=lyrics,
    )


def _write_flac_lyrics(audio: FLAC, lyrics: str) -> None:
    """Write lyrics to FLAC file."""
    audio["LYRICS"] = lyrics


def _write_ogg_lyrics(audio, lyrics: str) -> None:
    """Write lyrics to OGG file."""
    import base64
    encoded = base64.b64encode(lyrics.encode("utf-8")).decode("ascii")
    audio["LYRICSBASE64"] = encoded


def _write_m4a_lyrics(audio: MP4, lyrics: str) -> None:
    """Write lyrics to M4A file."""
    audio["\xa9lyr"] = lyrics


def _write_wave_lyrics(audio: WAVE, lyrics: str) -> None:
    """Write lyrics to WAV file (uses INFO tag)."""
    audio["INFO"] = lyrics


def read_lyrics_from_tag(file_path: Path) -> Optional[str]:
    """Read existing lyrics from audio file tags."""
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return None

        audio_type = _get_audio_type(audio)

        if audio_type == "MP3":
            if audio.tags and "USLT::eng" in audio.tags:
                return str(audio.tags["USLT::eng"].text[0])
        elif audio_type == "FLAC":
            if "LYRICS" in audio:
                return str(audio["LYRICS"])
        elif audio_type in ("OggVorbis", "OggSpeex", "OggOpus"):
            if "LYRICSBASE64" in audio:
                import base64
                return base64.b64decode(audio["LYRICSBASE64"]).decode("utf-8")
        elif audio_type == "MP4":
            if "\xa9lyr" in audio:
                return str(audio["\xa9lyr"])

        return None
    except Exception:
        return None


def save_lyrics_to_file(audio_path: Path, lyrics: str, lyrics_format: LyricsFormat = LyricsFormat.LRC) -> Path:
    """Save lyrics to a separate file next to the audio file."""
    suffix = lyrics_format.value
    lyrics_path = audio_path.with_suffix(f".{suffix}")
    lyrics_path.write_text(lyrics, encoding="utf-8")
    return lyrics_path


def convert_lrc_to_srt(lrc: str, offset_ms: int = 0) -> str:
    """Convert LRC format to SRT format."""
    from .provider import parse_lrc_timestamp

    lines = []
    srt_index = 1
    current_text = []

    for line in lrc.split("\n"):
        timestamp = parse_lrc_timestamp(line)
        if timestamp is not None:
            text = line.split("]",1)[1].strip() if "]" in line else ""
            if current_text and current_text[0]["timestamp"] is not None:
                start_ts = current_text[0]["timestamp"] * 1000 + offset_ms
                end_ts = timestamp * 1000 + offset_ms
                lines.append(_format_srt_entry(srt_index, start_ts, end_ts, current_text[0]["text"]))
                srt_index += 1
            current_text = [{"timestamp": timestamp, "text": text}]
        elif line.strip():
            if current_text:
                current_text[0]["text"] += line.strip()

    if current_text:
        last_ts = current_text[0]["timestamp"]
        lines.append(_format_srt_entry(srt_index, last_ts * 1000 + offset_ms, last_ts * 1000 + 5000 + offset_ms, current_text[0]["text"]))

    return "\n".join(lines)


def _format_srt_entry(index: int, start_ms: int, end_ms: int, text: str) -> str:
    """Format a single SRT entry."""
    start = _ms_to_srt_time(start_ms)
    end = _ms_to_srt_time(end_ms)
    return f"{index}\n{start} --> {end}\n{text}"


def _ms_to_srt_time(ms: float) -> str:
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
    ms_int = int(ms)
    hours = ms_int // 3600000
    ms_int %= 3600000
    minutes = ms_int // 60000
    ms_int %= 60000
    seconds = ms_int // 1000
    ms_int %= 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms_int:03d}"


def convert_lrc_to_ass(lrc: str, title: str = "", artist: str = "") -> str:
    """Convert LRC format to ASS subtitle format for karaoke display."""
    from .provider import parse_lrc_timestamp

    header = """[Script Info]
Title: {title}
ScriptType: v4.00+
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(title=title or "Lyrics")

    events = []
    for line in lrc.split("\n"):
        timestamp = parse_lrc_timestamp(line)
        if timestamp is not None:
            text = line.split("]", 1)[1].strip() if "]" in line else ""
            if text:
                start = _ms_to_ass_time(int(timestamp * 1000))
                end = _ms_to_ass_time(int(timestamp * 1000) + 5000)
                text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
                events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return header + "\n".join(events)


def _ms_to_ass_time(ms: int) -> str:
    """Convert milliseconds to ASS time format (H:MM:SS.cc)."""
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    centiseconds = (ms % 1000) // 10
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def clean_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    return re.sub(r'[<>:"/\\|?*]', "", name)