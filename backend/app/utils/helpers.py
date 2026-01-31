"""Helper utility functions."""


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to human-readable timestamp.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (MM:SS or HH:MM:SS)
    """
    if seconds is None:
        return "0:00"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def parse_timestamp(timestamp: str) -> float:
    """
    Parse a timestamp string to seconds.

    Args:
        timestamp: Timestamp string (MM:SS or HH:MM:SS)

    Returns:
        Time in seconds
    """
    parts = timestamp.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0.0


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split a list into chunks.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
