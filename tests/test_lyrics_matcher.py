"""Tests for lyrics_matcher package."""

import pytest
from pathlib import Path
from lyrics_matcher.provider import (
    parse_lrc_timestamp,
    format_lrc_timestamp,
    convert_to_enhanced_lrc,
    parse_enhanced_lrc,
    LrclibProvider,
    NeteaseProvider,
    QQMusicProvider,
    MultiProvider,
    LyricTrack,
)
from lyrics_matcher.audio import (
    is_supported_audio,
    AudioMetadata,
    get_metadata,
    LyricsFormat,
    convert_lrc_to_srt,
    convert_lrc_to_ass,
)


class TestLrcTimestamp:
    """Test LRC timestamp parsing and formatting."""

    def test_parse_timestamp(self):
        assert parse_lrc_timestamp("[00:12.34]") == pytest.approx(12.34)
        assert parse_lrc_timestamp("[01:30.00]") == pytest.approx(90.0)
        assert parse_lrc_timestamp("[03:45.5]") == pytest.approx(225.5)

    def test_format_timestamp(self):
        assert format_lrc_timestamp(12.34) == "[00:12.34]"
        assert format_lrc_timestamp(90.0) == "[01:30.00]"
        assert format_lrc_timestamp(225.5) == "[03:45.50]"


class TestAudioFormats:
    """Test audio format detection."""

    def test_supported_formats(self):
        assert is_supported_audio(Path("song.mp3")) is True
        assert is_supported_audio(Path("song.flac")) is True
        assert is_supported_audio(Path("song.ogg")) is True
        assert is_supported_audio(Path("song.m4a")) is True

    def test_unsupported_formats(self):
        assert is_supported_audio(Path("song.txt")) is False
        assert is_supported_audio(Path("song.jpg")) is False


class TestAudioMetadata:
    """Test audio metadata extraction."""

    def test_default_metadata(self):
        metadata = AudioMetadata()
        assert metadata.title is None
        assert metadata.artist is None
        assert metadata.duration == 0.0


class TestLyricsProviders:
    """Test lyrics providers."""

    def test_lrclib_provider_init(self):
        provider = LrclibProvider()
        assert provider.timeout == 10
        assert provider.name == "LRCLIB"

    def test_netease_provider_init(self):
        provider = NeteaseProvider()
        assert provider.timeout == 10
        assert provider.name == "Netease"

    def test_qqmusic_provider_init(self):
        provider = QQMusicProvider()
        assert provider.timeout == 10
        assert provider.name == "QQ Music"

    def test_multi_provider_init(self):
        provider = MultiProvider()
        assert provider.max_workers == 4
        assert len(provider.providers) == 3


class TestLyricTrack:
    """Test LyricTrack dataclass."""

    def test_track_creation(self):
        track = LyricTrack(
            id="test_1",
            name="Test Song",
            track_name="Test Song",
            artist_name="Test Artist",
            album_name="Test Album",
            duration=180.0,
            instrumental=False,
            source="LRCLIB",
        )
        assert track.name == "Test Song"
        assert track.artist_name == "Test Artist"
        assert track.duration == 180.0
        assert track.source == "LRCLIB"


class TestEnhancedLrc:
    """Test enhanced LRC conversion."""

    def test_parse_enhanced_lrc(self):
        lrc = "[00:12.00]<00:12.00>Hello<00:12.50>World"
        words = parse_enhanced_lrc(lrc)
        assert len(words) > 0

    def test_convert_to_enhanced_lrc(self):
        synced = """[00:12.00]Hello World
[00:15.00]This is a test"""
        result = convert_to_enhanced_lrc(synced)
        assert result is not None
        assert len(result) > 0


class TestSrtConversion:
    """Test SRT format conversion."""

    def test_convert_lrc_to_srt(self):
        lrc = """[00:00.00]First line
[00:05.00]Second line"""
        srt = convert_lrc_to_srt(lrc)
        assert "1" in srt
        assert "00:00:00,000 --> 00:00:05,000" in srt
        assert "First line" in srt


class TestAssConversion:
    """Test ASS format conversion."""

    def test_convert_lrc_to_ass(self):
        lrc = "[00:00.00]Hello World"
        ass = convert_lrc_to_ass(lrc, "Test Song", "Test Artist")
        assert "[Script Info]" in ass
        assert "[V4+ Styles]" in ass
        assert "[Events]" in ass


class TestLyricsFormat:
    """Test LyricsFormat enum."""

    def test_format_values(self):
        assert LyricsFormat.LRC.value == "lrc"
        assert LyricsFormat.SRT.value == "srt"
        assert LyricsFormat.ASS.value == "ass"

class TestI18n:
    """Test internationalization module."""

    def test_translations_exist(self):
        from lyrics_matcher.i18n import LANGUAGES, TRANSLATIONS
        assert "zh_CN" in LANGUAGES
        assert "en" in LANGUAGES
        assert "zh_CN" in TRANSLATIONS
        assert "en" in TRANSLATIONS

    def test_default_language(self):
        from lyrics_matcher.i18n import i18n
        assert i18n.get_language() == "zh_CN"

    def test_translate(self):
        from lyrics_matcher.i18n import t
        assert "歌词匹配器" in t("app_title") or "Lyrics Matcher" in t("app_title")

    def test_language_switch(self):
        from lyrics_matcher.i18n import i18n, set_language
        i18n.set_language("en")
        assert i18n.get_language() == "en"
        i18n.set_language("zh_CN")
        assert i18n.get_language() == "zh_CN"
