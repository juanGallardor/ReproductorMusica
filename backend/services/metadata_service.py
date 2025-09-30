import os
from typing import Dict, Any, Optional, Union
from mutagen import File as MutagenFile
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TCON
from mutagen.flac import FLAC, Picture
from mutagen.wave import WAVE
from mutagen import MutagenError


class MetadataService:
    """
    Service for handling audio metadata operations.
    
    This class provides comprehensive metadata extraction, editing,
    and cover art management using the mutagen library.
    """
    
    def __init__(self):
        """Initialize the metadata service."""
        self.supported_formats = {'.mp3', '.wav', '.flac'}
        
        # Field mapping for different formats
        self.field_mapping = {
            'mp3': {
                'title': 'TIT2',
                'artist': 'TPE1', 
                'album': 'TALB',
                'date': 'TDRC',
                'genre': 'TCON'
            },
            'flac': {
                'title': 'TITLE',
                'artist': 'ARTIST',
                'album': 'ALBUM', 
                'date': 'DATE',
                'genre': 'GENRE'
            },
            'wav': {
                'title': 'TIT2',
                'artist': 'TPE1',
                'album': 'TALB',
                'date': 'TDRC', 
                'genre': 'TCON'
            }
        }
    
    # METADATA EXTRACTION
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract complete metadata from audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dict[str, Any]: Complete metadata dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_format = self._get_file_format(file_path)
        if file_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_format}")
        
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                return self._get_empty_metadata()
            
            # Get basic info
            basic_info = self.get_basic_info(file_path)
            
            # Get technical info
            technical_info = self.get_technical_info(file_path)
            
            # Combine all metadata
            metadata = {
                **basic_info,
                **technical_info,
                'file_path': file_path,
                'format': file_format.lstrip('.'),
                'has_cover_art': self._has_cover_art(audio_file, file_format)
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
            return self._get_empty_metadata()
    
    def get_basic_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata information.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dict[str, Any]: Basic metadata (title, artist, album, duration)
        """
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                return self._get_empty_basic_info()
            
            file_format = self._get_file_format(file_path).lstrip('.')
            
            # Extract common fields
            title = self._extract_field(audio_file, 'title', file_format)
            artist = self._extract_field(audio_file, 'artist', file_format)
            album = self._extract_field(audio_file, 'album', file_format)
            date = self._extract_field(audio_file, 'date', file_format)
            genre = self._extract_field(audio_file, 'genre', file_format)
            
            # Get duration
            duration = getattr(audio_file.info, 'length', 0.0) if audio_file.info else 0.0
            
            return {
                'title': title or os.path.splitext(os.path.basename(file_path))[0],
                'artist': artist,
                'album': album,
                'year': self._parse_year(date),
                'genre': genre,
                'duration': duration
            }
            
        except Exception as e:
            print(f"Error getting basic info from {file_path}: {e}")
            return self._get_empty_basic_info()
    
    def get_technical_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract technical audio information.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dict[str, Any]: Technical info (bitrate, sample rate, etc.)
        """
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None or audio_file.info is None:
                return {}
            
            info = audio_file.info
            
            return {
                'bitrate': getattr(info, 'bitrate', 0),
                'sample_rate': getattr(info, 'sample_rate', 0),
                'channels': getattr(info, 'channels', 0),
                'bits_per_sample': getattr(info, 'bits_per_sample', 0),
                'file_size': os.path.getsize(file_path)
            }
            
        except Exception as e:
            print(f"Error getting technical info from {file_path}: {e}")
            return {}
    
    def has_metadata(self, file_path: str) -> bool:
        """
        Check if file has any metadata.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            bool: True if file has metadata, False otherwise
        """
        try:
            audio_file = MutagenFile(file_path)
            return audio_file is not None and len(audio_file.tags or {}) > 0
        except Exception:
            return False
    
    # METADATA EDITING
    
    def update_title(self, file_path: str, title: str) -> bool:
        """
        Update title metadata.
        
        Args:
            file_path: Path to audio file
            title: New title
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self._update_field(file_path, 'title', title)
    
    def update_artist(self, file_path: str, artist: str) -> bool:
        """
        Update artist metadata.
        
        Args:
            file_path: Path to audio file
            artist: New artist name
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self._update_field(file_path, 'artist', artist)
    
    def update_album(self, file_path: str, album: str) -> bool:
        """
        Update album metadata.
        
        Args:
            file_path: Path to audio file
            album: New album name
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self._update_field(file_path, 'album', album)
    
    def update_year(self, file_path: str, year: int) -> bool:
        """
        Update year metadata.
        
        Args:
            file_path: Path to audio file
            year: Year value
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self._update_field(file_path, 'date', str(year))
    
    def update_multiple_fields(self, file_path: str, metadata: Dict[str, str]) -> bool:
        """
        Update multiple metadata fields at once.
        
        Args:
            file_path: Path to audio file
            metadata: Dictionary of field:value pairs
            
        Returns:
            bool: True if all updates successful, False otherwise
        """
        try:
            file_format = self._get_file_format(file_path).lstrip('.')
            audio_file = MutagenFile(file_path)
            
            if audio_file is None:
                return False
            
            # Initialize tags if they don't exist
            if audio_file.tags is None:
                if file_format == 'mp3':
                    audio_file.add_tags()
                else:
                    audio_file.tags = {}
            
            # Update each field
            for field, value in metadata.items():
                if field in self.field_mapping.get(file_format, {}):
                    self._set_field_value(audio_file, field, value, file_format)
            
            audio_file.save()
            return True
            
        except Exception as e:
            print(f"Error updating metadata in {file_path}: {e}")
            return False
    
    # COVER ART MANAGEMENT
    
    def extract_cover_art(self, file_path: str) -> Optional[bytes]:
        """
        Extract embedded cover art.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Optional[bytes]: Cover art data if found, None otherwise
        """
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                return None
            
            file_format = self._get_file_format(file_path).lstrip('.')
            
            if file_format == 'mp3':
                return self._extract_mp3_cover(audio_file)
            elif file_format == 'flac':
                return self._extract_flac_cover(audio_file)
            elif file_format == 'wav':
                return self._extract_wav_cover(audio_file)
            
            return None
            
        except Exception as e:
            print(f"Error extracting cover art from {file_path}: {e}")
            return None
    
    def embed_cover_art(self, file_path: str, image_data: bytes, image_type: str = 'image/jpeg') -> bool:
        """
        Embed cover art into audio file.
        
        Args:
            file_path: Path to audio file
            image_data: Image data to embed
            image_type: MIME type of image
            
        Returns:
            bool: True if embedded successfully, False otherwise
        """
        try:
            file_format = self._get_file_format(file_path).lstrip('.')
            audio_file = MutagenFile(file_path)
            
            if audio_file is None:
                return False
            
            if file_format == 'mp3':
                return self._embed_mp3_cover(audio_file, image_data, image_type)
            elif file_format == 'flac':
                return self._embed_flac_cover(audio_file, image_data, image_type)
            elif file_format == 'wav':
                return self._embed_wav_cover(audio_file, image_data, image_type)
            
            return False
            
        except Exception as e:
            print(f"Error embedding cover art in {file_path}: {e}")
            return False
    
    def get_cover_art_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about embedded cover art.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dict[str, Any]: Cover art information
        """
        try:
            cover_data = self.extract_cover_art(file_path)
            
            if cover_data is None:
                return {'has_cover': False}
            
            return {
                'has_cover': True,
                'size': len(cover_data),
                'type': self._detect_image_type(cover_data)
            }
            
        except Exception:
            return {'has_cover': False}
    
    # UTILITIES
    
    def clean_metadata(self, file_path: str) -> bool:
        """
        Remove corrupted or invalid metadata tags.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            bool: True if cleaned successfully, False otherwise
        """
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                return False
            
            # Remove all tags and re-add clean ones
            if hasattr(audio_file, 'delete'):
                audio_file.delete()
            
            # Re-initialize with minimal tags
            basic_info = self.get_basic_info(file_path)
            self.update_multiple_fields(file_path, {
                'title': basic_info.get('title', ''),
                'artist': basic_info.get('artist', ''),
                'album': basic_info.get('album', '')
            })
            
            return True
            
        except Exception as e:
            print(f"Error cleaning metadata in {file_path}: {e}")
            return False
    
    def copy_metadata(self, source_path: str, target_path: str) -> bool:
        """
        Copy metadata from one file to another.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            bool: True if copied successfully, False otherwise
        """
        try:
            source_metadata = self.extract_metadata(source_path)
            
            # Copy basic fields
            fields_to_copy = ['title', 'artist', 'album', 'year', 'genre']
            metadata_dict = {field: source_metadata.get(field, '') 
                           for field in fields_to_copy 
                           if source_metadata.get(field)}
            
            return self.update_multiple_fields(target_path, metadata_dict)
            
        except Exception as e:
            print(f"Error copying metadata from {source_path} to {target_path}: {e}")
            return False
    
    # FORMAT-SPECIFIC METHODS
    
    def extract_mp3_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract MP3-specific metadata."""
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None or not hasattr(audio_file, 'tags'):
                return {}
            
            metadata = {}
            tags = audio_file.tags or {}
            
            # MP3-specific fields
            for tag_name, tag_obj in tags.items():
                if hasattr(tag_obj, 'text'):
                    metadata[tag_name] = str(tag_obj.text[0]) if tag_obj.text else ''
                else:
                    metadata[tag_name] = str(tag_obj)
            
            return metadata
            
        except Exception:
            return {}
    
    def extract_wav_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract WAV-specific metadata."""
        try:
            audio_file = WAVE(file_path)
            if audio_file.tags is None:
                return {}
            
            metadata = {}
            for tag_name, tag_value in audio_file.tags.items():
                metadata[tag_name] = str(tag_value[0]) if isinstance(tag_value, list) else str(tag_value)
            
            return metadata
            
        except Exception:
            return {}
    
    def extract_flac_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract FLAC-specific metadata."""
        try:
            audio_file = FLAC(file_path)
            if audio_file.tags is None:
                return {}
            
            metadata = {}
            for tag_name, tag_values in audio_file.tags.items():
                metadata[tag_name] = tag_values[0] if tag_values else ''
            
            return metadata
            
        except Exception:
            return {}
    
    # PRIVATE HELPER METHODS
    
    def _get_file_format(self, file_path: str) -> str:
        """Get file format from extension."""
        return os.path.splitext(file_path)[1].lower()
    
    def _extract_field(self, audio_file, field: str, file_format: str) -> Optional[str]:
        """Extract a specific field from audio file."""
        try:
            if audio_file.tags is None:
                return None
            
            field_mapping = self.field_mapping.get(file_format, {})
            field_name = field_mapping.get(field)
            
            if not field_name:
                return None
            
            if file_format == 'mp3':
                tag = audio_file.tags.get(field_name)
                return str(tag.text[0]) if tag and tag.text else None
            else:
                values = audio_file.tags.get(field_name, [])
                return values[0] if values else None
                
        except Exception:
            return None
    
    def _update_field(self, file_path: str, field: str, value: str) -> bool:
        """Update a specific field in audio file."""
        try:
            file_format = self._get_file_format(file_path).lstrip('.')
            audio_file = MutagenFile(file_path)
            
            if audio_file is None:
                return False
            
            # Initialize tags if needed
            if audio_file.tags is None:
                if file_format == 'mp3':
                    audio_file.add_tags()
                else:
                    audio_file.tags = {}
            
            self._set_field_value(audio_file, field, value, file_format)
            audio_file.save()
            
            return True
            
        except Exception as e:
            print(f"Error updating {field} in {file_path}: {e}")
            return False
    
    def _set_field_value(self, audio_file, field: str, value: str, file_format: str):
        """Set field value in audio file."""
        field_mapping = self.field_mapping.get(file_format, {})
        field_name = field_mapping.get(field)
        
        if not field_name:
            return
        
        if file_format == 'mp3':
            if field == 'title':
                audio_file.tags[field_name] = TIT2(encoding=3, text=value)
            elif field == 'artist':
                audio_file.tags[field_name] = TPE1(encoding=3, text=value)
            elif field == 'album':
                audio_file.tags[field_name] = TALB(encoding=3, text=value)
            elif field == 'date':
                audio_file.tags[field_name] = TDRC(encoding=3, text=value)
        else:
            audio_file.tags[field_name] = [value]
    
    def _has_cover_art(self, audio_file, file_format: str) -> bool:
        """Check if audio file has cover art."""
        try:
            if file_format == '.mp3':
                return 'APIC:' in audio_file.tags if audio_file.tags else False
            elif file_format == '.flac':
                return len(audio_file.pictures) > 0 if hasattr(audio_file, 'pictures') else False
            elif file_format == '.wav':
                return 'APIC:' in audio_file.tags if audio_file.tags else False
            return False
        except Exception:
            return False
    
    def _extract_mp3_cover(self, audio_file) -> Optional[bytes]:
        """Extract cover art from MP3."""
        try:
            for key in audio_file.tags.keys():
                if key.startswith('APIC:'):
                    return audio_file.tags[key].data
            return None
        except Exception:
            return None
    
    def _extract_flac_cover(self, audio_file) -> Optional[bytes]:
        """Extract cover art from FLAC."""
        try:
            if hasattr(audio_file, 'pictures') and audio_file.pictures:
                return audio_file.pictures[0].data
            return None
        except Exception:
            return None
    
    def _extract_wav_cover(self, audio_file) -> Optional[bytes]:
        """Extract cover art from WAV."""
        return self._extract_mp3_cover(audio_file)  # WAV uses same ID3 tags
    
    def _embed_mp3_cover(self, audio_file, image_data: bytes, image_type: str) -> bool:
        """Embed cover art in MP3."""
        try:
            if audio_file.tags is None:
                audio_file.add_tags()
            
            audio_file.tags['APIC'] = APIC(
                encoding=3,
                mime=image_type,
                type=3,  # Cover (front)
                desc='Cover',
                data=image_data
            )
            audio_file.save()
            return True
        except Exception:
            return False
    
    def _embed_flac_cover(self, audio_file, image_data: bytes, image_type: str) -> bool:
        """Embed cover art in FLAC."""
        try:
            picture = Picture()
            picture.data = image_data
            picture.type = 3  # Cover (front)
            picture.mime = image_type
            picture.desc = 'Cover'
            
            audio_file.clear_pictures()
            audio_file.add_picture(picture)
            audio_file.save()
            return True
        except Exception:
            return False
    
    def _embed_wav_cover(self, audio_file, image_data: bytes, image_type: str) -> bool:
        """Embed cover art in WAV."""
        return self._embed_mp3_cover(audio_file, image_data, image_type)
    
    def _detect_image_type(self, image_data: bytes) -> str:
        """Detect image type from binary data."""
        if image_data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif image_data.startswith(b'\x89PNG'):
            return 'image/png'
        elif image_data.startswith(b'WEBP'):
            return 'image/webp'
        return 'image/unknown'
    
    def _parse_year(self, date_str: Optional[str]) -> Optional[int]:
        """Parse year from date string."""
        if not date_str:
            return None
        try:
            return int(date_str[:4])
        except (ValueError, TypeError):
            return None
    
    def _get_empty_metadata(self) -> Dict[str, Any]:
        """Get empty metadata structure."""
        return {
            'title': '',
            'artist': '',
            'album': '',
            'year': None,
            'genre': '',
            'duration': 0.0,
            'bitrate': 0,
            'sample_rate': 0,
            'channels': 0,
            'file_size': 0,
            'has_cover_art': False
        }
    
    def _get_empty_basic_info(self) -> Dict[str, Any]:
        """Get empty basic info structure."""
        return {
            'title': '',
            'artist': '',
            'album': '',
            'year': None,
            'genre': '',
            'duration': 0.0
        }


# Example usage
if __name__ == "__main__":
    print("Metadata Service ready for professional audio metadata handling!")
    
    # Example usage (commented out since it requires actual audio files)
    """
    metadata_service = MetadataService()
    
    # Extract metadata
    metadata = metadata_service.extract_metadata("/path/to/song.mp3")
    print(f"Song title: {metadata.get('title')}")
    
    # Update metadata
    success = metadata_service.update_title("/path/to/song.mp3", "New Title")
    print(f"Title updated: {success}")
    
    # Extract cover art
    cover_data = metadata_service.extract_cover_art("/path/to/song.mp3")
    if cover_data:
        print(f"Cover art found: {len(cover_data)} bytes")
    """