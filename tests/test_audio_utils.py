"""Unit tests for okcourse audio utility functions."""

import io
import pytest

from okcourse.utils.audio_utils import _is_valid_mp3, combine_mp3_buffers


def test_is_valid_mp3_with_id3_header():
    """Test _is_valid_mp3 with ID3 header."""
    mp3_data_id3 = b"ID3\x03\x00\x00\x00\x00\x00\x00"  # Mock ID3 header
    assert _is_valid_mp3(mp3_data_id3) is True


def test_is_valid_mp3_with_frame_sync():
    """Test _is_valid_mp3 with frame sync pattern."""
    mp3_data_sync = b"\xff\xfb\x90\x00"  # Mock MP3 frame sync
    assert _is_valid_mp3(mp3_data_sync) is True


def test_is_valid_mp3_with_invalid_data():
    """Test _is_valid_mp3 with invalid data."""
    invalid_data = b"This is not MP3 data"
    assert _is_valid_mp3(invalid_data) is False


def test_is_valid_mp3_with_empty_data():
    """Test _is_valid_mp3 with empty data."""
    empty_data = b""
    assert _is_valid_mp3(empty_data) is False


def test_combine_mp3_buffers_empty_list():
    """Test combine_mp3_buffers with empty buffer list raises ValueError."""
    with pytest.raises(ValueError, match="No MP3 buffers provided"):
        combine_mp3_buffers([])


def test_combine_mp3_buffers_invalid_mp3():
    """Test combine_mp3_buffers with invalid MP3 data raises ValueError."""
    invalid_buffer = io.BytesIO(b"Not MP3 data")
    with pytest.raises(ValueError, match="Invalid MP3 buffer"):
        combine_mp3_buffers([invalid_buffer])


# Note: Testing the full combine_mp3_buffers function would require actual MP3 data
# and the mutagen library to work with real MP3 files. For a minimal test suite,
# we're focusing on the edge cases and validation logic that can be tested
# without requiring actual audio files.