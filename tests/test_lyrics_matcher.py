"""Tests for lyrics_matcher package."""

import pytest
from lyrics_matcher.provider import (
    parse_lrc_timestamp,
    format_lrc_timestamp,
    LrclibProvider,
)
from lyrics_matcher.audio import is_supported_audio, AudioMetadata, get_metadata
from pathlib import Path


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


class TestLrclibProvider:
    """Test Lrclib API provider."""

    def test_provider_initialization(self):
        provider = LrclibProvider()
        assert provider.timeout == 10

    def test_provider_custom_timeout(self):
        provider = LrclibProvider(timeout=30)
        assert provider.timeout == 30