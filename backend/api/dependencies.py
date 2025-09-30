"""
FastAPI Dependencies for Vinyl Music Player - VERSIÓN CORREGIDA
Academic Project - Software Patterns and Data Structures

Este módulo define dependency injection functions para FastAPI endpoints,
con una gestión centralizada y correcta de servicios.
"""

import os
import uuid
from typing import List
from fastapi import HTTPException, status

from patterns.singleton import MusicPlayerManager
from services.playlist_service import PlaylistService
from services.audio_service import AudioService
from services.file_service import FileService
from services.metadata_service import MetadataService
from patterns.abstract_factory import get_supported_formats as factory_get_supported_formats


# CUSTOM EXCEPTIONS
class PlaylistNotFoundError(HTTPException):
    """Exception raised when playlist is not found."""
    
    def __init__(self, playlist_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playlist with ID '{playlist_id}' not found"
        )


class SongNotFoundError(HTTPException):
    def __init__(self, song_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID '{song_id}' not found"
        )


class InvalidAudioFormatError(HTTPException):
    """Exception raised when audio format is not supported."""
    
    def __init__(self, format_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio format '{format_name}' is not supported. Supported formats: {', '.join(get_supported_formats())}"
        )


class InvalidVolumeError(HTTPException):
    """Exception raised when volume level is invalid."""
    
    def __init__(self, volume: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Volume level must be between 0 and 100, got {volume}"
        )


class FileNotFoundError(HTTPException):
    """Exception raised when file is not found."""
    
    def __init__(self, file_path: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}"
        )


# INSTANCIAS GLOBALES - CRÍTICO: Solo una instancia de cada servicio
_playlist_service: PlaylistService = None
_audio_service: AudioService = None
_file_service: FileService = None
_metadata_service: MetadataService = None


def get_music_player_manager() -> MusicPlayerManager:
    """Get the singleton music player manager instance."""
    return MusicPlayerManager.get_instance()

def get_playlist_service() -> PlaylistService:
    """
    Get the playlist service instance - VERSIÓN CON DEBUG COMPLETO.
    """
    global _playlist_service
    if _playlist_service is None:
        print("[DEPENDENCIES] Inicializando PlaylistService global por primera vez")
        _playlist_service = PlaylistService()
        _playlist_service.load_playlists_from_file()
        print(f"[DEPENDENCIES] PlaylistService inicializado con {len(_playlist_service.playlists)} playlists")
        for i, p in enumerate(_playlist_service.playlists):
            print(f"[DEPENDENCIES] Playlist {i}: ID='{p.id}', Name='{p.name}'")
    else:
        print(f"[DEPENDENCIES] Reutilizando PlaylistService existente con {len(_playlist_service.playlists)} playlists")
    
    # CRÍTICO: Verificar que las playlists están realmente cargadas
    print(f"[DEPENDENCIES] Verificación final: {len(_playlist_service.playlists)} playlists disponibles")
    return _playlist_service


def get_audio_service() -> AudioService:
    """Get the audio service instance."""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service


def get_file_service() -> FileService:
    """Get the file service instance."""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service


def get_metadata_service() -> MetadataService:
    """Get the metadata service instance."""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = MetadataService()
    return _metadata_service


# FUNCIÓN PARA FORZAR INICIALIZACIÓN
def initialize_global_services():
    global _playlist_service, _audio_service, _file_service, _metadata_service
    
    print("[DEPENDENCIES] Inicializando servicios globales...")
    
    # Inicializar cada servicio UNA SOLA VEZ
    if _playlist_service is None:
        _playlist_service = PlaylistService()
    if _audio_service is None:
        _audio_service = AudioService()
    if _file_service is None:
        _file_service = FileService()
    if _metadata_service is None:
        _metadata_service = MetadataService()
    
    print("[DEPENDENCIES] Todos los servicios globales inicializados correctamente")

# VALIDATION DEPENDENCIES
def validate_playlist_id_format(playlist_id: str) -> str:
    """Validate playlist ID format only (for new resource creation)."""
    if not playlist_id or not playlist_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist ID cannot be empty"
        )
    
    playlist_id = playlist_id.strip()
    
    # Validate UUID format
    try:
        uuid.UUID(playlist_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid playlist ID format. Must be a valid UUID."
        )
    
    return playlist_id


def validate_playlist_id(playlist_id: str) -> str:
    """Validate playlist ID format and existence - CON DEBUG."""
    print(f"[VALIDATE] ===== VALIDANDO PLAYLIST ID =====")
    print(f"[VALIDATE] ID recibido: '{playlist_id}'")
    print(f"[VALIDATE] Tipo: {type(playlist_id)}")
    print(f"[VALIDATE] Repr: {repr(playlist_id)}")
    
    # First validate format
    playlist_id = validate_playlist_id_format(playlist_id)
    print(f"[VALIDATE] ID después de validar formato: '{playlist_id}'")
    
    # Then check if playlist exists usando el servicio global
    playlist_service = get_playlist_service()
    print(f"[VALIDATE] Obtenido playlist_service con {len(playlist_service.playlists)} playlists")
    
    playlist = playlist_service.get_playlist_by_id(playlist_id)
    print(f"[VALIDATE] Resultado de búsqueda: {playlist is not None}")
    
    if playlist is None:
        print(f"[VALIDATE] ❌ Playlist no encontrada, lanzando excepción")
        raise PlaylistNotFoundError(playlist_id)
    
    print(f"[VALIDATE] ✅ Playlist encontrada: {playlist.name}")
    return playlist_id


def validate_song_id_format(song_id: str) -> str:
    """Validate song ID format only."""
    if not song_id or not song_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Song ID cannot be empty"
        )
    
    song_id = song_id.strip()
    
    # Validate UUID format
    try:
        uuid.UUID(song_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid song ID format. Must be a valid UUID."
        )
    
    return song_id


def validate_song_id(song_id: str) -> str:
    """Validate song ID format."""
    return validate_song_id_format(song_id)


def validate_volume_level(volume: float) -> float:
    """Validate volume level."""
    if not isinstance(volume, (int, float)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Volume must be a number"
        )
    
    if not 0 <= volume <= 100:
        raise InvalidVolumeError(volume)
    
    return float(volume)


def validate_position(position: int, max_position: int) -> int:
    """Validate position in playlist."""
    if not isinstance(position, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Position must be an integer"
        )
    
    if position < 0 or position >= max_position:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Position must be between 0 and {max_position - 1}"
        )
    
    return position


def validate_audio_format(file_extension: str) -> str:
    """Validate audio file format."""
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension cannot be empty"
        )
    
    # Normalize extension
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    file_extension = file_extension.lower()
    
    supported_formats = get_supported_formats()
    if file_extension not in supported_formats:
        raise InvalidAudioFormatError(file_extension)
    
    return file_extension


def validate_file_path(file_path: str) -> str:
    """Validate file path exists and is accessible."""
    if not file_path or not file_path.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path cannot be empty"
        )
    
    file_path = file_path.strip()
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a file: {file_path}"
        )
    
    return file_path


# CONFIGURATION DEPENDENCIES
def get_upload_directory() -> str:
    """Get the upload directory path."""
    upload_dir = os.environ.get('UPLOAD_DIRECTORY', 'frontend/static/uploads')
    
    # Ensure directory exists
    os.makedirs(upload_dir, exist_ok=True)
    
    return upload_dir


def get_supported_formats() -> List[str]:
    """Get list of supported audio formats."""
    return factory_get_supported_formats()


def get_data_directory() -> str:
    """Get the data directory path for storing JSON files."""
    data_dir = os.environ.get('DATA_DIRECTORY', 'data')
    
    # Ensure directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    return data_dir


def get_max_file_size() -> int:
    """Get maximum allowed file size for uploads."""
    max_size = os.environ.get('MAX_FILE_SIZE', '52428800')  # 50MB default
    try:
        return int(max_size)
    except ValueError:
        return 52428800  # 50MB fallback


def get_allowed_image_formats() -> List[str]:
    """Get list of allowed image formats for cover art."""
    return ['.jpg', '.jpeg', '.png', '.webp', '.gif']


# UTILITY DEPENDENCIES
def validate_search_query(query: str) -> str:
    """Validate and clean search query."""
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    query = query.strip()
    
    if len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters long"
        )
    
    if len(query) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot exceed 100 characters"
        )
    
    return query


def validate_pagination(page: int = 1, limit: int = 20) -> tuple[int, int]:
    """Validate pagination parameters."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be 1 or greater"
        )
    
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    return page, limit


def validate_playlist_name(name: str) -> str:
    """Validate playlist name."""
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist name cannot be empty"
        )
    
    name = name.strip()
    
    if len(name) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist name must be at least 1 character long"
        )
    
    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playlist name cannot exceed 100 characters"
        )
    
    return name


# DEPENDENCY CLEANUP
def cleanup_services():
    """Clean up service instances and resources."""
    global _audio_service, _file_service, _metadata_service, _playlist_service
    
    try:
        if _audio_service:
            _audio_service.cleanup()
            _audio_service = None
        
        # Reset other services
        _file_service = None
        _metadata_service = None
        _playlist_service = None
        
        print("Services cleaned up successfully")
        
    except Exception as e:
        print(f"Error during service cleanup: {e}")


# HEALTH CHECK AND UTILITY FUNCTIONS
def health_check_dependencies() -> dict:
    """Perform health check on all dependencies."""
    health_status = {}
    
    try:
        # Test MusicPlayerManager
        player_manager = get_music_player_manager()
        health_status['music_player_manager'] = 'healthy'
    except Exception as e:
        health_status['music_player_manager'] = f'error: {e}'
    
    try:
        # Test PlaylistService
        playlist_service = get_playlist_service()
        health_status['playlist_service'] = f'healthy ({len(playlist_service.playlists)} playlists loaded)'
    except Exception as e:
        health_status['playlist_service'] = f'error: {e}'
    
    try:
        # Test AudioService
        audio_service = get_audio_service()
        health_status['audio_service'] = 'healthy'
    except Exception as e:
        health_status['audio_service'] = f'error: {e}'
    
    try:
        # Test FileService
        file_service = get_file_service()
        health_status['file_service'] = 'healthy'
    except Exception as e:
        health_status['file_service'] = f'error: {e}'
    
    try:
        # Test MetadataService
        metadata_service = get_metadata_service()
        health_status['metadata_service'] = 'healthy'
    except Exception as e:
        health_status['metadata_service'] = f'error: {e}'
    
    return health_status