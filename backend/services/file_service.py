import os
import shutil
import mimetypes
import uuid
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

from models.song import Song
from patterns.abstract_factory import get_factory, is_supported_format, get_supported_formats


class UnsupportedFormatError(Exception):
    """Custom exception for unsupported audio formats."""
    pass


class FileService:
    """
    Service for handling file operations related to audio files.
    
    This class provides comprehensive file management capabilities
    including validation, loading, and cover image handling.
    """
    
    def __init__(self, uploads_directory: str = "frontend/static/uploads"):
        """
        Initialize the file service.
        
        Args:
            uploads_directory: Directory for storing uploaded files
        """
        self.uploads_directory = uploads_directory
        self.cover_images_directory = os.path.join(uploads_directory, "covers")
        
        # Create directories if they don't exist
        os.makedirs(self.uploads_directory, exist_ok=True)
        os.makedirs(self.cover_images_directory, exist_ok=True)
        
        # Supported audio formats
        self.supported_formats = set(get_supported_formats())
        
        # Image formats for covers
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    
    # FILE VALIDATION
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate if a file is a valid audio file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            bool: True if valid audio file, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            if not os.path.isfile(file_path):
                return False
            
            # Check file extension
            file_format = self.get_file_format(file_path)
            if not self.is_supported_format(file_format):
                return False
            
            # Check file size (must be > 0)
            if os.path.getsize(file_path) == 0:
                return False
            
            # Use factory to validate format-specific details
            try:
                factory = get_factory(file_format)
                return factory.validate_file_format(file_path)
            except Exception:
                return False
            
        except Exception:
            return False
    
    def get_file_format(self, file_path: str) -> str:
        """
        Get the file format from file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: File extension (e.g., '.mp3')
        """
        return os.path.splitext(file_path)[1].lower()
    
    def is_supported_format(self, file_extension: str) -> bool:
        """
        Check if a file extension is supported.
        
        Args:
            file_extension: File extension to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return is_supported_format(file_extension)
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            int: File size in bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return os.path.getsize(file_path)
    
    # FILE LOADING
    
    def load_audio_file(self, file_path: str) -> Song:
        """
        Load an audio file and create a Song object.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Song: Created Song object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnsupportedFormatError: If format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        file_format = self.get_file_format(file_path)
        if not self.is_supported_format(file_format):
            raise UnsupportedFormatError(f"Unsupported audio format: {file_format}")
        
        try:
            factory = get_factory(file_format)
            song = factory.create_song(file_path)
            return song
        except Exception as e:
            raise UnsupportedFormatError(f"Failed to load audio file: {e}")
    
    def load_multiple_files(self, file_paths: List[str]) -> List[Song]:
        """
        Load multiple audio files.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            List[Song]: List of successfully loaded songs
        """
        songs = []
        
        for file_path in file_paths:
            try:
                song = self.load_audio_file(file_path)
                songs.append(song)
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
                continue
        
        return songs
    
    def scan_directory_for_audio(self, directory_path: str) -> List[str]:
        """
        Scan a directory for audio files.
        
        Args:
            directory_path: Path to directory to scan
            
        Returns:
            List[str]: List of audio file paths found
        """
        if not os.path.exists(directory_path):
            return []
        
        audio_files = []
        
        try:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.validate_audio_file(file_path):
                        audio_files.append(file_path)
        except Exception:
            pass
        
        return sorted(audio_files)
    
    # COVER IMAGE MANAGEMENT
    # En file_service.py, reemplaza el método save_cover_image:

    def save_cover_image(self, song_id: str, image_data: bytes, image_format: str = 'jpg') -> str:
        """
        Save cover image data to file - VERSIÓN MEJORADA que acepta cualquier formato.
        
        Args:
            song_id: ID of the song/playlist this cover belongs to
            image_data: Binary image data
            image_format: Image format (cualquier formato)
            
        Returns:
            str: Path to saved image file (siempre .jpg)
            
        Raises:
            ValueError: If image data is invalid
        """
        if not image_data:
            raise ValueError("Image data cannot be empty")
        
        print(f"[FILE_SERVICE] Saving cover image for {song_id}")
        print(f"[FILE_SERVICE] Original format: {image_format}")
        print(f"[FILE_SERVICE] Image size: {len(image_data)} bytes")
        
        try:
            # Intentar convertir la imagen a JPG usando PIL/Pillow
            from PIL import Image
            import io
            
            # Abrir imagen desde bytes
            image = Image.open(io.BytesIO(image_data))
            print(f"[FILE_SERVICE] Original image format: {image.format}")
            print(f"[FILE_SERVICE] Original image size: {image.size}")
            
            # Convertir a RGB si es necesario (para JPG)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Crear fondo blanco para transparencias
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Redimensionar si es muy grande (máximo 800x800)
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"[FILE_SERVICE] Resized to: {image.size}")
            
            # Guardar como JPG
            filename = f"cover_{song_id}.jpg"
            file_path = os.path.join(self.cover_images_directory, filename)
            
            # Guardar con calidad alta
            image.save(file_path, 'JPEG', quality=90, optimize=True)
            
            print(f"[FILE_SERVICE] Cover saved successfully: {file_path}")
            
            # Verificar que se guardó
            if os.path.exists(file_path):
                saved_size = os.path.getsize(file_path)
                print(f"[FILE_SERVICE] Saved file size: {saved_size} bytes")
                return file_path
            else:
                raise ValueError("File was not saved properly")
            
        except ImportError:
            # Si no tiene PIL/Pillow, usar método simple
            print(f"[FILE_SERVICE] PIL not available, using simple save")
            
            # Forzar extensión .jpg
            filename = f"cover_{song_id}.jpg"
            file_path = os.path.join(self.cover_images_directory, filename)
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                return file_path
            except Exception as e:
                raise ValueError(f"Failed to save cover image: {e}")
        
        except Exception as e:
            print(f"[FILE_SERVICE] Error processing image: {e}")
            # Fallback: guardar tal como está
            filename = f"cover_{song_id}.jpg"
            file_path = os.path.join(self.cover_images_directory, filename)
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                print(f"[FILE_SERVICE] Saved without conversion: {file_path}")
                return file_path
            except Exception as e2:
                raise ValueError(f"Failed to save cover image: {e2}")
    
    def extract_embedded_cover(self, audio_file_path: str) -> Optional[bytes]:
        """
        Extract embedded cover art from audio file.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Optional[bytes]: Cover image data if found, None otherwise
        """
        # This is a simplified implementation
        # Real implementation would use libraries like mutagen
        
        if not self.validate_audio_file(audio_file_path):
            return None
        
        # For now, return None as we don't have metadata extraction libraries
        # In a real implementation, you would use:
        # - mutagen for MP3/FLAC
        # - Other libraries for WAV
        
        return None
    
    # BASIC FILE OPERATIONS
    
    def copy_file_to_uploads(self, source_path: str) -> str:
        """
        Copy a file to the uploads directory.
        
        Args:
            source_path: Path to source file
            
        Returns:
            str: Path to copied file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        filename = os.path.basename(source_path)
        filename = self.clean_filename(filename)
        
        # Generate unique filename if file already exists
        base_name, extension = os.path.splitext(filename)
        target_path = os.path.join(self.uploads_directory, filename)
        
        if os.path.exists(target_path):
            unique_filename = self.generate_unique_filename(base_name, extension)
            target_path = os.path.join(self.uploads_directory, unique_filename)
        
        try:
            shutil.copy2(source_path, target_path)
            return target_path
        except Exception as e:
            raise RuntimeError(f"Failed to copy file: {e}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    # UTILITIES
    
    def get_audio_files_in_directory(self, directory: str) -> List[str]:
        """
        Get all audio files in a directory (non-recursive).
        
        Args:
            directory: Directory path to search
            
        Returns:
            List[str]: List of audio file paths
        """
        if not os.path.exists(directory):
            return []
        
        audio_files = []
        
        try:
            for item in os.listdir(directory):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path) and self.validate_audio_file(file_path):
                    audio_files.append(file_path)
        except Exception:
            pass
        
        return sorted(audio_files)
    
    def clean_filename(self, filename: str) -> str:
        """
        Clean a filename to be safe for filesystem.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Cleaned filename
        """
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Ensure it's not empty
        if not filename:
            filename = 'unnamed_file'
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def generate_unique_filename(self, base_name: str, extension: str) -> str:
        """
        Generate a unique filename by adding a counter.
        
        Args:
            base_name: Base name without extension
            extension: File extension
            
        Returns:
            str: Unique filename
        """
        counter = 1
        while True:
            filename = f"{base_name}_{counter}{extension}"
            file_path = os.path.join(self.uploads_directory, filename)
            
            if not os.path.exists(file_path):
                return filename
            
            counter += 1
            
            # Safety limit
            if counter > 9999:
                # Use UUID as fallback
                unique_id = str(uuid.uuid4())[:8]
                return f"{base_name}_{unique_id}{extension}"
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict[str, Any]: File information dictionary
        """
        if not os.path.exists(file_path):
            return {"exists": False}
        
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                "exists": True,
                "path": file_path,
                "filename": os.path.basename(file_path),
                "size": stat.st_size,
                "format": self.get_file_format(file_path),
                "mime_type": mime_type,
                "is_audio": self.validate_audio_file(file_path),
                "modified_time": stat.st_mtime,
                "created_time": stat.st_ctime
            }
        except Exception:
            return {"exists": True, "error": "Failed to get file info"}
    
    def validate_cover_image(self, image_path: str) -> bool:
        """
        Validate if a file is a valid cover image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            bool: True if valid image, False otherwise
        """
        if not os.path.exists(image_path):
            return False
        
        try:
            extension = os.path.splitext(image_path)[1].lower()
            if extension not in self.supported_image_formats:
                return False
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type and not mime_type.startswith('image/'):
                return False
            
            # Check file size (should be reasonable for an image)
            size = os.path.getsize(image_path)
            if size == 0 or size > 10 * 1024 * 1024:  # Max 10MB
                return False
            
            return True
            
        except Exception:
            return False
    
    def create_backup_copy(self, file_path: str) -> Optional[str]:
        """
        Create a backup copy of a file.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Optional[str]: Path to backup file if successful, None otherwise
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            backup_path = file_path + '.backup'
            counter = 1
            
            while os.path.exists(backup_path):
                backup_path = f"{file_path}.backup{counter}"
                counter += 1
            
            shutil.copy2(file_path, backup_path)
            return backup_path
            
        except Exception:
            return None
    
    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary files in uploads directory.
        
        Returns:
            int: Number of files cleaned up
        """
        cleanup_count = 0
        
        try:
            for root, _, files in os.walk(self.uploads_directory):
                for file in files:
                    if file.startswith('.tmp') or file.endswith('.tmp'):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            cleanup_count += 1
                        except Exception:
                            continue
        except Exception:
            pass
        
        return cleanup_count


# Example usage
if __name__ == "__main__":
    print("File Service ready for handling audio files!")
    
    # Example usage (commented out since it requires actual files)
    """
    file_service = FileService()
    
    # Validate an audio file
    is_valid = file_service.validate_audio_file("/path/to/song.mp3")
    print(f"File is valid: {is_valid}")
    
    # Load an audio file
    try:
        song = file_service.load_audio_file("/path/to/song.mp3")
        print(f"Loaded song: {song.title}")
    except Exception as e:
        print(f"Error loading song: {e}")
    
    # Scan directory for audio files
    audio_files = file_service.scan_directory_for_audio("/path/to/music")
    print(f"Found {len(audio_files)} audio files")
    """