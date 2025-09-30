import os
import math
from pathlib import Path
from typing import List, Optional

# Type hint for Song model (will be imported when needed)
try:
    from ..models.song import Song
except ImportError:
    # For standalone testing
    Song = None

# Constants
SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac']
DEFAULT_VOLUME = 70.0
MAX_VOLUME = 100.0
MIN_VOLUME = 0.0


def seconds_to_mmss(seconds: float) -> str:
    """
    Convert seconds to MM:SS format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted time string (e.g., "3:45")
        
    Examples:
        >>> seconds_to_mmss(225.5)
        "3:45"
        >>> seconds_to_mmss(65)
        "1:05"
    """
    if seconds < 0:
        return "0:00"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    return f"{minutes}:{remaining_seconds:02d}"


def seconds_to_hhmmss(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted time string (e.g., "1:23:45")
        
    Examples:
        >>> seconds_to_hhmmss(5025)
        "1:23:45"
        >>> seconds_to_hhmmss(225)
        "0:03:45"
    """
    if seconds < 0:
        return "0:00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    
    return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"


def mmss_to_seconds(time_str: str) -> float:
    """
    Convert MM:SS format to seconds.
    
    Args:
        time_str: Time string in MM:SS format
        
    Returns:
        Duration in seconds
        
    Examples:
        >>> mmss_to_seconds("3:45")
        225.0
        >>> mmss_to_seconds("1:05")
        65.0
    """
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        else:
            return 0.0
    except (ValueError, AttributeError):
        return 0.0


def format_duration(seconds: float) -> str:
    """
    Format duration with smart formatting.
    Uses MM:SS for durations under 1 hour, HH:MM:SS for longer.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Appropriately formatted time string
    """
    if seconds < 3600:  # Less than 1 hour
        return seconds_to_mmss(seconds)
    else:
        return seconds_to_hhmmss(seconds)


def bytes_to_mb(bytes_size: int) -> float:
    """
    Convert bytes to megabytes.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Size in megabytes (rounded to 2 decimal places)
    """
    if bytes_size < 0:
        return 0.0
    
    mb = bytes_size / (1024 * 1024)
    return round(mb, 2)


def format_file_size(bytes_size: int) -> str:
    """
    Format file size with appropriate unit.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string (e.g., "5.2 MB", "1.3 GB")
    """
    if bytes_size < 0:
        return "0 B"
    
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        kb = bytes_size / 1024
        return f"{kb:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        mb = bytes_size / (1024 * 1024)
        return f"{mb:.1f} MB"
    else:
        gb = bytes_size / (1024 * 1024 * 1024)
        return f"{gb:.1f} GB"


def is_valid_audio_extension(extension: str) -> bool:
    """
    Check if file extension is supported for audio.
    
    Args:
        extension: File extension (with or without dot)
        
    Returns:
        True if extension is supported
    """
    if not extension:
        return False
    
    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = '.' + extension
    
    return extension.lower() in SUPPORTED_FORMATS


def is_valid_volume(volume: float) -> bool:
    """
    Check if volume level is valid.
    
    Args:
        volume: Volume level (0-100)
        
    Returns:
        True if volume is in valid range
    """
    return MIN_VOLUME <= volume <= MAX_VOLUME


def is_valid_position(position: float, duration: float) -> bool:
    """
    Check if playback position is valid for given duration.
    
    Args:
        position: Playback position in seconds
        duration: Total duration in seconds
        
    Returns:
        True if position is valid
    """
    if duration <= 0:
        return position == 0
    
    return 0 <= position <= duration


def calculate_playlist_duration(songs: List) -> float:
    """
    Calculate total duration of all songs in playlist.
    
    Args:
        songs: List of Song objects
        
    Returns:
        Total duration in seconds
    """
    if not songs:
        return 0.0
    
    total_duration = 0.0
    for song in songs:
        if hasattr(song, 'duration') and song.duration:
            total_duration += song.duration
    
    return total_duration


def calculate_average_bitrate(songs: List) -> float:
    """
    Calculate average bitrate of songs in playlist.
    Note: This is a placeholder implementation.
    Real bitrate calculation would require audio file analysis.
    
    Args:
        songs: List of Song objects
        
    Returns:
        Average bitrate (estimated)
    """
    if not songs:
        return 0.0
    
    # Placeholder calculation based on file format
    total_bitrate = 0.0
    count = 0
    
    for song in songs:
        if hasattr(song, 'format') and song.format:
            # Estimated bitrates by format
            if song.format.lower() == 'mp3':
                total_bitrate += 320.0  # kbps
            elif song.format.lower() == 'wav':
                total_bitrate += 1411.0  # kbps
            elif song.format.lower() == 'flac':
                total_bitrate += 1000.0  # kbps
            count += 1
    
    return total_bitrate / count if count > 0 else 0.0


def normalize_file_path(file_path: str) -> str:
    """
    Normalize file path for consistent usage.
    
    Args:
        file_path: Original file path
        
    Returns:
        Normalized path string
    """
    if not file_path:
        return ""
    
    # Convert to Path object and resolve
    path = Path(file_path)
    
    # Return absolute path as string
    return str(path.resolve())


def get_audio_file_extension(file_path: str) -> str:
    """
    Extract file extension from audio file path.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        File extension with dot (e.g., ".mp3")
    """
    if not file_path:
        return ""
    
    path = Path(file_path)
    return path.suffix.lower()


def extract_filename_without_extension(file_path: str) -> str:
    """
    Extract filename without extension from file path.
    
    Args:
        file_path: Path to file
        
    Returns:
        Filename without extension
    """
    if not file_path:
        return ""
    
    path = Path(file_path)
    return path.stem


def detect_audio_format(file_path: str) -> str:
    """
    Detect audio format from file extension.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Audio format (mp3, wav, flac) or empty string if unsupported
    """
    extension = get_audio_file_extension(file_path)
    
    if extension in SUPPORTED_FORMATS:
        return extension[1:]  # Remove the dot
    
    return ""


def get_supported_formats() -> List[str]:
    """
    Get list of supported audio formats.
    
    Returns:
        List of supported file extensions
    """
    return SUPPORTED_FORMATS.copy()


def validate_audio_file(file_path: str) -> tuple[bool, str]:
    """
    Comprehensive validation of audio file.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "File path is empty"
    
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, "File does not exist"
    
    # Check if it's a file (not directory)
    if not path.is_file():
        return False, "Path is not a file"
    
    # Check file extension
    extension = path.suffix.lower()
    if not is_valid_audio_extension(extension):
        return False, f"Unsupported file format: {extension}"
    
    # Check file size (minimum 1KB for valid audio)
    if path.stat().st_size < 1024:
        return False, "File is too small to be valid audio"
    
    return True, "File is valid"


def get_file_info(file_path: str) -> dict:
    """
    Get basic file information for audio file.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dictionary with file information
    """
    if not file_path or not Path(file_path).exists():
        return {}
    
    path = Path(file_path)
    stat = path.stat()
    
    return {
        'filename': path.name,
        'filename_without_ext': path.stem,
        'extension': path.suffix.lower(),
        'format': detect_audio_format(file_path),
        'size_bytes': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'size_mb': bytes_to_mb(stat.st_size),
        'absolute_path': str(path.resolve()),
        'is_valid_audio': is_valid_audio_extension(path.suffix)
    }


# Helper functions for common operations
def clamp_volume(volume: float) -> float:
    """
    Clamp volume to valid range.
    
    Args:
        volume: Volume level
        
    Returns:
        Volume clamped to valid range (0-100)
    """
    return max(MIN_VOLUME, min(MAX_VOLUME, volume))


def clamp_position(position: float, duration: float) -> float:
    """
    Clamp playback position to valid range.
    
    Args:
        position: Playback position in seconds
        duration: Total duration in seconds
        
    Returns:
        Position clamped to valid range
    """
    if duration <= 0:
        return 0.0
    
    return max(0.0, min(duration, position))


def calculate_progress_percentage(position: float, duration: float) -> float:
    """
    Calculate playback progress as percentage.
    
    Args:
        position: Current position in seconds
        duration: Total duration in seconds
        
    Returns:
        Progress percentage (0-100)
    """
    if duration <= 0:
        return 0.0
    
    progress = (position / duration) * 100
    return max(0.0, min(100.0, progress))


def percentage_to_position(percentage: float, duration: float) -> float:
    """
    Convert percentage to playback position.
    
    Args:
        percentage: Progress percentage (0-100)
        duration: Total duration in seconds
        
    Returns:
        Position in seconds
    """
    if duration <= 0:
        return 0.0
    
    clamped_percentage = max(0.0, min(100.0, percentage))
    return (clamped_percentage / 100.0) * duration