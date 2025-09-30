import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Constants
SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
DEFAULT_ENCODING = 'utf-8'


def ensure_file_exists(file_path: str) -> bool:
    """
    Check if file exists.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file exists, False otherwise
    """
    if not file_path:
        return False
    
    try:
        return Path(file_path).exists() and Path(file_path).is_file()
    except (OSError, ValueError):
        return False


def copy_file_safe(source: str, destination: str) -> bool:
    """
    Safely copy file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if copy was successful, False otherwise
    """
    if not source or not destination:
        return False
    
    try:
        source_path = Path(source)
        destination_path = Path(destination)
        
        # Check if source file exists
        if not source_path.exists() or not source_path.is_file():
            return False
        
        # Ensure destination directory exists
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source, destination)
        
        # Verify copy was successful
        return destination_path.exists()
        
    except (OSError, shutil.Error, ValueError) as e:
        print(f"Error copying file: {e}")
        return False


def delete_file_safe(file_path: str) -> bool:
    """
    Safely delete file.
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    if not file_path:
        return False
    
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return True  # File doesn't exist, consider it "deleted"
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return False
        
        # Delete file
        path.unlink()
        
        # Verify deletion
        return not path.exists()
        
    except (OSError, ValueError) as e:
        print(f"Error deleting file: {e}")
        return False


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        True if directory exists or was created successfully
    """
    if not directory_path:
        return False
    
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return path.exists() and path.is_dir()
        
    except (OSError, ValueError) as e:
        print(f"Error creating directory: {e}")
        return False


def list_files_in_directory(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    List files in directory, optionally filtered by extensions.
    
    Args:
        directory: Directory path
        extensions: List of file extensions to filter (e.g., ['.mp3', '.wav'])
        
    Returns:
        List of file paths matching criteria
    """
    if not directory:
        return []
    
    try:
        path = Path(directory)
        
        # Check if directory exists
        if not path.exists() or not path.is_dir():
            return []
        
        files = []
        
        # Get all files in directory
        for file_path in path.iterdir():
            if file_path.is_file():
                # Filter by extensions if provided
                if extensions:
                    if file_path.suffix.lower() in [ext.lower() for ext in extensions]:
                        files.append(str(file_path))
                else:
                    files.append(str(file_path))
        
        # Sort files alphabetically
        files.sort()
        return files
        
    except (OSError, ValueError) as e:
        print(f"Error listing files in directory: {e}")
        return []


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    if not file_path:
        return {}
    
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return {'exists': False, 'error': 'File does not exist'}
        
        stat = path.stat()
        
        return {
            'exists': True,
            'name': path.name,
            'stem': path.stem,
            'suffix': path.suffix,
            'absolute_path': str(path.resolve()),
            'parent_directory': str(path.parent),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'accessed_at': datetime.fromtimestamp(stat.st_atime),
            'is_file': path.is_file(),
            'is_directory': path.is_dir(),
            'is_audio': path.suffix.lower() in SUPPORTED_FORMATS,
            'is_image': path.suffix.lower() in SUPPORTED_IMAGE_FORMATS
        }
        
    except (OSError, ValueError) as e:
        return {'exists': False, 'error': str(e)}


def get_file_modification_date(file_path: str) -> Optional[datetime]:
    """
    Get file modification date.
    
    Args:
        file_path: Path to file
        
    Returns:
        datetime object of modification time, None if error
    """
    if not file_path:
        return None
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        stat = path.stat()
        return datetime.fromtimestamp(stat.st_mtime)
        
    except (OSError, ValueError):
        return None


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary with JSON data, empty dict if error
    """
    if not file_path:
        return {}
    
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            print(f"JSON file does not exist: {file_path}")
            return {}
        
        # Read and parse JSON
        with open(path, 'r', encoding=DEFAULT_ENCODING) as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
            
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return {}


def write_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Write data to JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to write
        indent: JSON indentation level
        
    Returns:
        True if write was successful, False otherwise
    """
    if not file_path or data is None:
        return False
    
    try:
        path = Path(file_path)
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON file
        with open(path, 'w', encoding=DEFAULT_ENCODING) as file:
            json.dump(data, file, indent=indent, ensure_ascii=False, default=str)
        
        # Verify file was written
        return path.exists()
        
    except (OSError, TypeError, ValueError) as e:
        print(f"Error writing JSON file {file_path}: {e}")
        return False


def get_audio_files_in_directory(directory: str) -> List[str]:
    """
    Get all audio files in directory.
    
    Args:
        directory: Directory path
        
    Returns:
        List of audio file paths
    """
    return list_files_in_directory(directory, SUPPORTED_FORMATS)


def get_image_files_in_directory(directory: str) -> List[str]:
    """
    Get all image files in directory.
    
    Args:
        directory: Directory path
        
    Returns:
        List of image file paths
    """
    return list_files_in_directory(directory, SUPPORTED_IMAGE_FORMATS)


def create_backup_file(file_path: str, backup_suffix: str = '.backup') -> bool:
    """
    Create backup copy of file.
    
    Args:
        file_path: Original file path
        backup_suffix: Suffix for backup file
        
    Returns:
        True if backup was created successfully
    """
    if not file_path:
        return False
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            return False
        
        backup_path = path.with_suffix(path.suffix + backup_suffix)
        return copy_file_safe(str(path), str(backup_path))
        
    except (OSError, ValueError):
        return False


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem
    """
    if not filename:
        return ""
    
    # Characters not allowed in filenames
    invalid_chars = '<>:"/\\|?*'
    
    cleaned = filename
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Remove extra spaces and dots
    cleaned = cleaned.strip(' .')
    
    # Ensure filename is not empty
    if not cleaned:
        cleaned = "untitled"
    
    return cleaned


def get_unique_filename(directory: str, base_name: str, extension: str = '') -> str:
    """
    Generate unique filename in directory.
    
    Args:
        directory: Target directory
        base_name: Base filename
        extension: File extension (with or without dot)
        
    Returns:
        Unique filename that doesn't exist in directory
    """
    if not directory or not base_name:
        return ""
    
    # Ensure extension starts with dot
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    
    # Clean base name
    clean_base = clean_filename(base_name)
    
    # Try original name first
    full_name = clean_base + extension
    full_path = Path(directory) / full_name
    
    if not full_path.exists():
        return full_name
    
    # Add number suffix if file exists
    counter = 1
    while True:
        numbered_name = f"{clean_base}_{counter}{extension}"
        numbered_path = Path(directory) / numbered_name
        
        if not numbered_path.exists():
            return numbered_name
        
        counter += 1
        
        # Safety limit
        if counter > 9999:
            return f"{clean_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"


def get_file_size_formatted(file_path: str) -> str:
    """
    Get formatted file size string.
    
    Args:
        file_path: Path to file
        
    Returns:
        Formatted size string (e.g., "5.2 MB")
    """
    info = get_file_info(file_path)
    
    if not info.get('exists'):
        return "0 B"
    
    size = info.get('size_bytes', 0)
    
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        kb = size / 1024
        return f"{kb:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        mb = size / (1024 * 1024)
        return f"{mb:.1f} MB"
    else:
        gb = size / (1024 * 1024 * 1024)
        return f"{gb:.1f} GB"


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """
    Validate file path for safety and existence.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "File path is empty"
    
    try:
        path = Path(file_path)
        
        # Check for path traversal attempts
        resolved_path = path.resolve()
        if '..' in str(path):
            return False, "Path traversal not allowed"
        
        # Check if path is too long
        if len(str(resolved_path)) > 260:  # Windows path limit
            return False, "Path is too long"
        
        return True, "Path is valid"
        
    except (OSError, ValueError) as e:
        return False, f"Invalid path: {e}"


def ensure_project_directories() -> bool:
    """
    Ensure all required project directories exist.
    
    Returns:
        True if all directories were created/exist
    """
    directories = [
        'data',
        'frontend/static/uploads',
        'frontend/static/images',
        'frontend/static/css',
        'frontend/static/js'
    ]
    
    success = True
    for directory in directories:
        if not ensure_directory_exists(directory):
            print(f"Failed to create directory: {directory}")
            success = False
    
    return success


def get_project_file_stats() -> Dict[str, Any]:
    """
    Get statistics about project files.
    
    Returns:
        Dictionary with file statistics
    """
    stats = {
        'audio_files': 0,
        'playlists': 0,
        'total_size': 0,
        'directories': [],
        'last_scan': datetime.now()
    }
    
    try:
        # Count audio files in uploads
        uploads_dir = 'frontend/static/uploads'
        if Path(uploads_dir).exists():
            audio_files = get_audio_files_in_directory(uploads_dir)
            stats['audio_files'] = len(audio_files)
            
            # Calculate total size
            for audio_file in audio_files:
                info = get_file_info(audio_file)
                stats['total_size'] += info.get('size_bytes', 0)
        
        # Count playlists
        playlists_file = 'data/playlists.json'
        if Path(playlists_file).exists():
            playlists_data = read_json_file(playlists_file)
            stats['playlists'] = len(playlists_data.get('playlists', []))
        
        # List directories
        for item in Path('.').iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                stats['directories'].append(item.name)
                
    except Exception as e:
        print(f"Error getting project stats: {e}")
    
    return stats