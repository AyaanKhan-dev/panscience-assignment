"""Tests for utility functions."""
import pytest

from app.utils.helpers import format_timestamp, truncate_text, parse_timestamp, chunk_list


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_zero_seconds(self):
        """Test formatting zero seconds."""
        assert format_timestamp(0) == "0:00"

    def test_seconds_only(self):
        """Test formatting seconds less than a minute."""
        assert format_timestamp(30) == "0:30"
        assert format_timestamp(59) == "0:59"

    def test_minutes_and_seconds(self):
        """Test formatting minutes and seconds."""
        assert format_timestamp(60) == "1:00"
        assert format_timestamp(90) == "1:30"
        assert format_timestamp(125) == "2:05"

    def test_hours(self):
        """Test formatting with hours."""
        assert format_timestamp(3600) == "1:00:00"
        assert format_timestamp(3665) == "1:01:05"
        assert format_timestamp(7325) == "2:02:05"

    def test_none_value(self):
        """Test formatting None value."""
        assert format_timestamp(None) == "0:00"

    def test_float_values(self):
        """Test formatting float values."""
        assert format_timestamp(90.5) == "1:30"
        assert format_timestamp(90.9) == "1:30"


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_short_text(self):
        """Test text shorter than max length."""
        text = "Hello world"
        assert truncate_text(text, 50) == "Hello world"

    def test_exact_length(self):
        """Test text exactly at max length."""
        text = "Hello"
        assert truncate_text(text, 5) == "Hello"

    def test_long_text(self):
        """Test text longer than max length."""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_empty_text(self):
        """Test empty text."""
        assert truncate_text("", 10) == ""

    def test_none_text(self):
        """Test None text."""
        assert truncate_text(None, 10) is None

    def test_custom_suffix(self):
        """Test custom suffix."""
        text = "This is a long text"
        result = truncate_text(text, 15, suffix="[more]")
        assert result.endswith("[more]")


class TestParseTimestamp:
    """Tests for parse_timestamp function."""

    def test_minutes_seconds(self):
        """Test parsing MM:SS format."""
        assert parse_timestamp("1:30") == 90
        assert parse_timestamp("0:45") == 45
        assert parse_timestamp("10:00") == 600

    def test_hours_minutes_seconds(self):
        """Test parsing HH:MM:SS format."""
        assert parse_timestamp("1:00:00") == 3600
        assert parse_timestamp("1:30:45") == 5445
        assert parse_timestamp("2:15:30") == 8130

    def test_invalid_format(self):
        """Test invalid format."""
        assert parse_timestamp("invalid") == 0.0
        assert parse_timestamp("") == 0.0


class TestChunkList:
    """Tests for chunk_list function."""

    def test_basic_chunking(self):
        """Test basic list chunking."""
        lst = [1, 2, 3, 4, 5, 6]
        chunks = chunk_list(lst, 2)
        assert chunks == [[1, 2], [3, 4], [5, 6]]

    def test_uneven_chunks(self):
        """Test chunking with remainder."""
        lst = [1, 2, 3, 4, 5]
        chunks = chunk_list(lst, 2)
        assert chunks == [[1, 2], [3, 4], [5]]

    def test_single_chunk(self):
        """Test when chunk size >= list length."""
        lst = [1, 2, 3]
        chunks = chunk_list(lst, 10)
        assert chunks == [[1, 2, 3]]

    def test_empty_list(self):
        """Test chunking empty list."""
        chunks = chunk_list([], 5)
        assert chunks == []

    def test_chunk_size_one(self):
        """Test chunk size of 1."""
        lst = [1, 2, 3]
        chunks = chunk_list(lst, 1)
        assert chunks == [[1], [2], [3]]
