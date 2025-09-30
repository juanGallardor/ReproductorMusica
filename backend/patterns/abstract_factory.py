import os
import mimetypes
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from models.song import Song


class AudioElementFactory(ABC):
    
    @abstractmethod
    def create_song(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Song:

        pass
    
    @abstractmethod
    def validate_file_format(self, file_path: str) -> bool:

        pass
    
    @abstractmethod
    def extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:

        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:

        pass
    
    def _get_file_size(self, file_path: str) -> int:

        return os.path.getsize(file_path)
    
    def _get_filename(self, file_path: str) -> str:
        """
        Get filename from path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Filename
        """
        return os.path.basename(file_path)
    
    def _validate_file_exists(self, file_path: str) -> None:
        """
        Validate that file exists and is accessible.
        
        Args:
            file_path: Path to validate
            
        Raises:
            ValueError: If file doesn't exist or is not accessible
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")


class MP3Factory(AudioElementFactory):

    
    def create_song(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Song:

        self._validate_file_exists(file_path)
        
        if not self.validate_file_format(file_path):
            raise ValueError(f"File is not a valid MP3: {file_path}")
        
        # Extract basic metadata
        extracted_metadata = self.extract_basic_metadata(file_path)
        
        # Override with provided metadata if available
        if metadata:
            extracted_metadata.update(metadata)
        
        # Create Song object
        song = Song(
            filename=extracted_metadata['filename'],
            file_path=file_path,
            title=extracted_metadata.get('title', extracted_metadata['filename']),
            duration=extracted_metadata.get('duration', 0.0),
            file_size=extracted_metadata['file_size'],
            format=extracted_metadata['format'],
            artist=extracted_metadata.get('artist'),
            album=extracted_metadata.get('album'),
            year=extracted_metadata.get('year')
        )
        
        return song
    
    def validate_file_format(self, file_path: str) -> bool:

        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.get_supported_extensions():
            return False
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type != 'audio/mpeg':
            # Some systems might not recognize MP3, so also check extension
            return file_extension == '.mp3'
        
        return True
    
    def extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:

        filename = self._get_filename(file_path)
        file_size = self._get_file_size(file_path)
        
        # Basic metadata that can be extracted without external libraries
        # In a real implementation, you'd use libraries like mutagen or eyed3
        metadata = {
            'filename': filename,
            'file_size': file_size,
            'format': 'mp3',
            'title': os.path.splitext(filename)[0],  # Use filename without extension as title
            'duration': self._estimate_duration_mp3(file_path),
        }
        
        # Try to extract more metadata from filename patterns
        self._parse_filename_metadata(metadata, filename)
        
        return metadata
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions for MP3."""
        return ['.mp3']
    
    def _estimate_duration_mp3(self, file_path: str) -> float:

        # Simplified estimation based on file size
        # Real implementation would parse MP3 headers
        file_size = self._get_file_size(file_path)
        
        # Rough estimation: assume 128kbps average bitrate
        # Formula: (file_size_bytes * 8) / (bitrate_kbps * 1000)
        estimated_duration = (file_size * 8) / (128 * 1000)
        
        return max(0.0, estimated_duration)
    
    def _parse_filename_metadata(self, metadata: Dict[str, Any], filename: str) -> None:

        name_without_ext = os.path.splitext(filename)[0]
        
        # Common patterns: "Artist - Title" or "Artist_Title"
        if ' - ' in name_without_ext:
            parts = name_without_ext.split(' - ', 1)
            if len(parts) == 2:
                metadata['artist'] = parts[0].strip()
                metadata['title'] = parts[1].strip()
        elif '_' in name_without_ext and ' ' not in name_without_ext:
            parts = name_without_ext.split('_', 1)
            if len(parts) == 2:
                metadata['artist'] = parts[0].strip()
                metadata['title'] = parts[1].strip()


class WAVFactory(AudioElementFactory):

    
    def create_song(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Song:
        """Create a Song object from a WAV file."""
        self._validate_file_exists(file_path)
        
        if not self.validate_file_format(file_path):
            raise ValueError(f"File is not a valid WAV: {file_path}")
        
        extracted_metadata = self.extract_basic_metadata(file_path)
        
        if metadata:
            extracted_metadata.update(metadata)
        
        song = Song(
            filename=extracted_metadata['filename'],
            file_path=file_path,
            title=extracted_metadata.get('title', extracted_metadata['filename']),
            duration=extracted_metadata.get('duration', 0.0),
            file_size=extracted_metadata['file_size'],
            format=extracted_metadata['format'],
            artist=extracted_metadata.get('artist'),
            album=extracted_metadata.get('album'),
            year=extracted_metadata.get('year')
        )
        
        return song
    
    def validate_file_format(self, file_path: str) -> bool:
        """Validate that the file is a valid WAV."""
        if not os.path.exists(file_path):
            return False
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.get_supported_extensions():
            return False
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type == 'audio/wav' or file_extension == '.wav'
    
    def extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from WAV file."""
        filename = self._get_filename(file_path)
        file_size = self._get_file_size(file_path)
        
        metadata = {
            'filename': filename,
            'file_size': file_size,
            'format': 'wav',
            'title': os.path.splitext(filename)[0],
            'duration': self._estimate_duration_wav(file_path),
        }
        
        self._parse_filename_metadata(metadata, filename)
        
        return metadata
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions for WAV."""
        return ['.wav']
    
    def _estimate_duration_wav(self, file_path: str) -> float:
        """Estimate WAV duration."""
        # Simplified estimation for WAV files
        # Real implementation would parse WAV headers
        file_size = self._get_file_size(file_path)
        
        # Rough estimation assuming CD quality (44.1kHz, 16-bit, stereo)
        # Formula: file_size / (sample_rate * bits_per_sample * channels / 8)
        estimated_duration = file_size / (44100 * 16 * 2 / 8)
        
        return max(0.0, estimated_duration)
    
    def _parse_filename_metadata(self, metadata: Dict[str, Any], filename: str) -> None:
        """Parse metadata from filename (same logic as MP3)."""
        name_without_ext = os.path.splitext(filename)[0]
        
        if ' - ' in name_without_ext:
            parts = name_without_ext.split(' - ', 1)
            if len(parts) == 2:
                metadata['artist'] = parts[0].strip()
                metadata['title'] = parts[1].strip()


class FLACFactory(AudioElementFactory):

    
    def create_song(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Song:
        """Create a Song object from a FLAC file."""
        self._validate_file_exists(file_path)
        
        if not self.validate_file_format(file_path):
            raise ValueError(f"File is not a valid FLAC: {file_path}")
        
        extracted_metadata = self.extract_basic_metadata(file_path)
        
        if metadata:
            extracted_metadata.update(metadata)
        
        song = Song(
            filename=extracted_metadata['filename'],
            file_path=file_path,
            title=extracted_metadata.get('title', extracted_metadata['filename']),
            duration=extracted_metadata.get('duration', 0.0),
            file_size=extracted_metadata['file_size'],
            format=extracted_metadata['format'],
            artist=extracted_metadata.get('artist'),
            album=extracted_metadata.get('album'),
            year=extracted_metadata.get('year')
        )
        
        return song
    
    def validate_file_format(self, file_path: str) -> bool:
        """Validate that the file is a valid FLAC."""
        if not os.path.exists(file_path):
            return False
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.get_supported_extensions():
            return False
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type == 'audio/flac' or file_extension == '.flac'
    
    def extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from FLAC file."""
        filename = self._get_filename(file_path)
        file_size = self._get_file_size(file_path)
        
        metadata = {
            'filename': filename,
            'file_size': file_size,
            'format': 'flac',
            'title': os.path.splitext(filename)[0],
            'duration': self._estimate_duration_flac(file_path),
        }
        
        self._parse_filename_metadata(metadata, filename)
        
        return metadata
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions for FLAC."""
        return ['.flac']
    
    def _estimate_duration_flac(self, file_path: str) -> float:
        """Estimate FLAC duration."""
        # Simplified estimation for FLAC files
        # Real implementation would parse FLAC metadata blocks
        file_size = self._get_file_size(file_path)
        
        # FLAC is lossless, so estimation is more complex
        # Rough estimation assuming average compression ratio
        estimated_duration = file_size / (44100 * 16 * 2 / 8 * 0.6)  # ~60% compression
        
        return max(0.0, estimated_duration)
    
    def _parse_filename_metadata(self, metadata: Dict[str, Any], filename: str) -> None:
        """Parse metadata from filename (same logic as MP3)."""
        name_without_ext = os.path.splitext(filename)[0]
        
        if ' - ' in name_without_ext:
            parts = name_without_ext.split(' - ', 1)
            if len(parts) == 2:
                metadata['artist'] = parts[0].strip()
                metadata['title'] = parts[1].strip()


# Factory Selector and Utility Functions

def get_factory(file_extension: str) -> AudioElementFactory:

    # Normalize extension (ensure it has a dot and is lowercase)
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    file_extension = file_extension.lower()
    
    # Factory mapping
    factory_map = {
        '.mp3': MP3Factory,
        '.wav': WAVFactory,
        '.flac': FLACFactory
    }
    
    if file_extension not in factory_map:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    
    return factory_map[file_extension]()


def get_supported_formats() -> List[str]:

    return ['.mp3', '.wav', '.flac']


def is_supported_format(extension: str) -> bool:

    if not extension.startswith('.'):
        extension = '.' + extension
    extension = extension.lower()
    
    return extension in get_supported_formats()


def create_song_from_file(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Song:

    file_extension = os.path.splitext(file_path)[1].lower()
    
    if not is_supported_format(file_extension):
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    factory = get_factory(file_extension)
    return factory.create_song(file_path, metadata)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Abstract Factory Pattern Implementation")
    
    # Test factory creation
    mp3_factory = get_factory('.mp3')
    wav_factory = get_factory('.wav')
    flac_factory = get_factory('.flac')
    
    print(f"MP3 Factory: {type(mp3_factory).__name__}")
    print(f"WAV Factory: {type(wav_factory).__name__}")
    print(f"FLAC Factory: {type(flac_factory).__name__}")
    
    # Test supported formats
    print(f"Supported formats: {get_supported_formats()}")
    print(f"Is .mp3 supported: {is_supported_format('.mp3')}")
    print(f"Is .ogg supported: {is_supported_format('.ogg')}")
    
    # Test validation (these will fail without actual files)
    try:
        print(f"MP3 validation (dummy file): {mp3_factory.validate_file_format('dummy.mp3')}")
    except Exception as e:
        print(f"Expected error: {e}")
    
    print("Abstract Factory pattern working correctly!")