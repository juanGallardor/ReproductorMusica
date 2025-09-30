import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, validator

from models.playlist import Playlist
from models.song import Song
from services.playlist_service import PlaylistService
from services.file_service import FileService
from services.metadata_service import MetadataService
from api.dependencies import (
    get_playlist_service,
    get_file_service,
    get_metadata_service,
    validate_playlist_id,
    validate_song_id,
    validate_search_query,
    validate_pagination,
    validate_playlist_name,
    validate_audio_format,
    get_upload_directory,
    get_allowed_image_formats,
    get_supported_formats,
    get_max_file_size,
    PlaylistNotFoundError,
    SongNotFoundError
)

# Create router
router = APIRouter(prefix="/playlists", tags=["playlists"])


# PYDANTIC MODELS

class PlaylistBase(BaseModel):
    """Base playlist model with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Playlist name")
    description: Optional[str] = Field(None, max_length=500, description="Playlist description")
    
    @validator('name')
    def validate_name(cls, v):
        return validate_playlist_name(v)
    
    @validator('description')
    def strip_description(cls, v):
        return v.strip() if v else None


class PlaylistCreate(PlaylistBase):
    """Model for creating a new playlist."""
    pass


class PlaylistUpdate(BaseModel):
    """Model for updating playlist information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_name(cls, v):
        return validate_playlist_name(v) if v else v
    
    @validator('description')
    def strip_description(cls, v):
        return v.strip() if v else v


class PlaylistResponse(BaseModel):
    """Model for playlist response."""
    id: str
    name: str
    description: Optional[str]
    cover_image: Optional[str]
    song_count: int
    total_duration: float
    total_duration_formatted: str
    created_at: str
    
    class Config:
        from_attributes = True


class SongInPlaylistResponse(BaseModel):
    """Model for song within playlist context."""
    id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    year: Optional[int]
    duration: float
    duration_formatted: str
    format: str
    filename: str
    position: int
    display_name: str


class PlaylistDetailResponse(PlaylistResponse):
    """Detailed playlist response with songs."""
    songs: List[SongInPlaylistResponse]
    current_position: int
    is_current_playlist: bool


class AddSongRequest(BaseModel):
    """Model for adding song to playlist."""
    song_id: str = Field(..., description="ID of the song to add")
    position: Optional[int] = Field(None, description="Position to insert at (0-indexed, None = end)")
    
    @validator('song_id')
    def validate_song_id(cls, v):
        return validate_song_id(v)


class ReorderRequest(BaseModel):
    """Model for reordering songs in playlist."""
    from_position: int = Field(..., ge=0, description="Current position of the song")
    to_position: int = Field(..., ge=0, description="Target position for the song")


class PlaylistSearchResponse(BaseModel):
    """Model for playlist search results."""
    playlists: List[PlaylistResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool


class ExportResponse(BaseModel):
    """Model for playlist export response."""
    playlist_name: str
    export_format: str
    songs: List[Dict[str, Any]]
    total_songs: int
    total_duration: float


# MAIN PLAYLIST ENDPOINTS

@router.get("/", response_model=List[PlaylistResponse])
async def list_playlists(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get list of all playlists.
    
    Returns paginated list of playlists with basic information.
    """
    try:
        page, limit = validate_pagination(page, limit)
        
        all_playlists = playlist_service.get_all_playlists()
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_playlists = all_playlists[start_idx:end_idx]
        
        # Convert to response models
        response_playlists = [
            PlaylistResponse(
                id=playlist.id,
                name=playlist.name,
                description=playlist.description,
                cover_image=playlist.cover_image,
                song_count=playlist.song_count,
                total_duration=playlist.total_duration,
                total_duration_formatted=playlist.get_total_duration_formatted(),
                created_at=playlist.created_at.isoformat()
            )
            for playlist in paginated_playlists
        ]
        
        return response_playlists
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving playlists: {str(e)}"
        )


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get detailed information about a specific playlist.
    
    Returns complete playlist information including all songs.
    """
    try:
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(str(playlist_id))
        
        # Get songs with position information
        songs_with_position = []
        songs_list = playlist.get_songs_list()
        
        for idx, song in enumerate(songs_list):
            songs_with_position.append(
                SongInPlaylistResponse(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    year=song.year,
                    duration=song.duration,
                    duration_formatted=song.get_duration_formatted(),
                    format=song.format,
                    filename=song.filename,
                    position=idx,
                    display_name=song.get_display_name()
                )
            )
        
        # Check if this is the current playlist
        from patterns.singleton import MusicPlayerManager
        player_manager = MusicPlayerManager.get_instance()
        is_current = (player_manager.current_playlist is not None and 
            player_manager.current_playlist.id == playlist_id)
        
        return PlaylistDetailResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            cover_image=playlist.cover_image,
            song_count=playlist.song_count,
            total_duration=playlist.total_duration,
            total_duration_formatted=playlist.get_total_duration_formatted(),
            created_at=playlist.created_at.isoformat(),
            songs=songs_with_position,
            current_position=playlist.current_position,
            is_current_playlist=is_current
        )
        
    except PlaylistNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving playlist: {str(e)}"
        )

# En playlists.py, actualiza el endpoint de crear playlist con más debug:

@router.post("/", response_model=PlaylistResponse)
async def create_playlist(
    playlist_data: PlaylistCreate,
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Create a new playlist - CON DEBUG MEJORADO.
    """
    try:
        print(f"[CREATE] ===== CREATING PLAYLIST =====")
        print(f"[CREATE] Name: '{playlist_data.name}'")
        print(f"[CREATE] Description: '{playlist_data.description}'")
        
        # Validar datos de entrada
        if not playlist_data.name or not playlist_data.name.strip():
            print(f"[CREATE] ERROR: Empty name")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Playlist name cannot be empty"
            )
        
        name_clean = playlist_data.name.strip()
        description_clean = playlist_data.description.strip() if playlist_data.description else ""
        
        print(f"[CREATE] Clean name: '{name_clean}'")
        print(f"[CREATE] Clean description: '{description_clean}'")
        
        playlist = playlist_service.create_playlist(
            name=name_clean,
            description=description_clean
        )
        
        print(f"[CREATE] Created playlist: {playlist.id} - {playlist.name}")
        
        return PlaylistResponse(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            cover_image=playlist.cover_image,
            song_count=playlist.song_count,
            total_duration=playlist.total_duration,
            total_duration_formatted=playlist.get_total_duration_formatted(),
            created_at=playlist.created_at.isoformat()
        )
        
    except ValueError as e:
        print(f"[CREATE] ValueError: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"[CREATE] Error creating playlist: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating playlist: {str(e)}"
        )

@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Delete a playlist - VERSIÓN COMPLETAMENTE CORREGIDA.
    """
    try:
        print(f"[DELETE] ===== EJECUTANDO DELETE =====")
        print(f"[DELETE] Playlist ID: {playlist_id}")
        
        # Ya sabemos que la playlist existe por validate_playlist_id
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        playlist_name = playlist.name if playlist else "Unknown"
        
        print(f"[DELETE] Llamando playlist_service.delete_playlist...")
        success = playlist_service.delete_playlist(playlist_id)
        print(f"[DELETE] delete_playlist retornó: {success}")
        
        if not success:
            print(f"[DELETE] ERROR: delete_playlist retornó False")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "type": "DeleteFailed",
                        "status_code": 400,
                        "message": "Failed to delete playlist",
                        "playlist_id": playlist_id
                    }
                }
            )
        
        print(f"[DELETE] ===== DELETE EXITOSO =====")
        return {
            "message": "Playlist deleted successfully", 
            "playlist_id": playlist_id,
            "deleted_playlist_name": playlist_name
        }
        
    except HTTPException as e:
        print(f"[DELETE] HTTPException: {e.detail}")
        raise
    except Exception as e:
        print(f"[DELETE] Exception inesperada: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "InternalError",
                    "status_code": 500,
                    "message": f"Internal server error: {str(e)}",
                    "playlist_id": playlist_id
                }
            }
        )

# SONG MANAGEMENT IN PLAYLISTS

@router.get("/{playlist_id}/songs", response_model=List[SongInPlaylistResponse])
async def get_playlist_songs(
    playlist_id: str = Depends(validate_playlist_id),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get songs from a specific playlist.
    
    Returns paginated list of songs in the playlist with position information.
    """
    try:
        page, limit = validate_pagination(page, limit)
        
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(str(playlist_id))
        
        songs_list = playlist.get_songs_list()
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_songs = songs_list[start_idx:end_idx]
        
        # Convert to response models with position
        response_songs = [
            SongInPlaylistResponse(
                id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                year=song.year,
                duration=song.duration,
                duration_formatted=song.get_duration_formatted(),
                format=song.format,
                filename=song.filename,
                position=start_idx + idx,
                display_name=song.get_display_name()
            )
            for idx, song in enumerate(paginated_songs)
        ]
        
        return response_songs
        
    except PlaylistNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving playlist songs: {str(e)}"
        )


def add_song(self, song: Song, position: Optional[int] = None) -> bool:
    """
    Add a song to the playlist.
    """
    if not isinstance(song, Song):
        print(f"[PLAYLIST] ERROR: Invalid song object: {type(song)}")
        raise ValueError("Invalid song object")
    
    try:
        print(f"[PLAYLIST] Adding song '{song.title}' to playlist '{self.name}'")
        print(f"[PLAYLIST] Current songs count: {self.songs.size()}")
        print(f"[PLAYLIST] Position: {position}")
        
        if position is None:
            # Add to end of playlist
            print(f"[PLAYLIST] Adding to end of playlist")
            self.songs.insert_at_end(song)
        else:
            # Add at specific position
            if position < 0 or position > self.songs.size():
                print(f"[PLAYLIST] ERROR: Invalid position {position}. Must be between 0 and {self.songs.size()}")
                raise ValueError(f"Invalid position {position}. Must be between 0 and {self.songs.size()}")
            print(f"[PLAYLIST] Adding at position {position}")
            self.songs.insert_at_position(song, position)
        
        print(f"[PLAYLIST] Song added to DoublyLinkedList. New size: {self.songs.size()}")
        
        self.update_totals()
        print(f"[PLAYLIST] Totals updated. New song_count: {self.song_count}")
        
        # Set as current if this is the first song
        if self.songs.size() == 1:
            self.current_position = 0
            self.songs.set_current(0)
            print(f"[PLAYLIST] Set as first song and current position")
        
        print(f"[PLAYLIST] Successfully added song '{song.title}'")
        return True
        
    except Exception as e:
        print(f"[PLAYLIST] Error adding song: {e}")
        import traceback
        traceback.print_exc()
        return False

@router.post("/{playlist_id}/upload-and-add")
async def upload_and_add_to_playlist(
    file: UploadFile = File(..., description="Audio file to upload"),
    playlist_id: str = Depends(validate_playlist_id),
    title: Optional[str] = Form(None),
    artist: Optional[str] = Form(None),
    album: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    file_service: FileService = Depends(get_file_service),
    metadata_service: MetadataService = Depends(get_metadata_service),
    upload_dir: str = Depends(get_upload_directory),
    max_file_size: int = Depends(get_max_file_size)
):
    """Upload an audio file and add it directly to a playlist - VERSIÓN CON DEBUG COMPLETO"""
    
    print(f"[UPLOAD] ===== STARTING UPLOAD PROCESS =====")
    print(f"[UPLOAD] Playlist ID: {playlist_id}")
    print(f"[UPLOAD] File: {file.filename}")
    print(f"[UPLOAD] File size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    # PASO 1: Verificar playlist service
    print(f"[UPLOAD] Playlist service has {len(playlist_service.playlists)} playlists")
    print(f"[UPLOAD] Available playlist IDs: {[p.id for p in playlist_service.playlists]}")
    
    # PASO 2: Buscar playlist
    playlist = playlist_service.get_playlist_by_id(playlist_id)
    if playlist is None:
        print(f"[UPLOAD] ERROR: Playlist not found: {playlist_id}")
        print(f"[UPLOAD] Service playlists: {[(p.id, p.name) for p in playlist_service.playlists]}")
        raise PlaylistNotFoundError(str(playlist_id))
    
    print(f"[UPLOAD] Found playlist: {playlist.name}")
    print(f"[UPLOAD] Playlist current songs: {playlist.song_count}")

    # PASO 3: Validar archivo
    if not file.filename:
        print("[UPLOAD] ERROR: No filename provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    print(f"[UPLOAD] Uploading file: {file.filename}")

    file_extension = os.path.splitext(file.filename)[1].lower()
    print(f"[UPLOAD] File extension: {file_extension}")
    
    try:
        validate_audio_format(file_extension)
        print(f"[UPLOAD] Audio format validation: PASSED")
    except Exception as e:
        print(f"[UPLOAD] Audio format validation: FAILED - {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio format. Supported: {get_supported_formats()}"
        )

    temp_path = None
    try:
        # PASO 4: Guardar archivo
        clean_filename = file_service.clean_filename(file.filename)
        temp_path = os.path.join(upload_dir, clean_filename)
        
        print(f"[UPLOAD] Clean filename: {clean_filename}")
        print(f"[UPLOAD] Target path: {temp_path}")
        print(f"[UPLOAD] Upload directory exists: {os.path.exists(upload_dir)}")
        
        if os.path.exists(temp_path):
            base_name, ext = os.path.splitext(clean_filename)
            unique_filename = file_service.generate_unique_filename(base_name, ext)
            temp_path = os.path.join(upload_dir, unique_filename)
            print(f"[UPLOAD] File exists, using unique name: {temp_path}")

        print(f"[UPLOAD] Reading file content...")
        content = await file.read()
        print(f"[UPLOAD] File content read: {len(content)} bytes")
        
        print(f"[UPLOAD] Writing to disk...")
        with open(temp_path, "wb") as buffer:
            buffer.write(content)
        
        # Verificar que el archivo se guardó
        if os.path.exists(temp_path):
            actual_size = os.path.getsize(temp_path)
            print(f"[UPLOAD] File saved successfully: {actual_size} bytes")
        else:
            print(f"[UPLOAD] ERROR: File was not saved to disk")
            raise HTTPException(status_code=500, detail="Failed to save file")

        # PASO 5: Cargar canción usando FileService
        print(f"[UPLOAD] Loading song from file using FileService...")
        print(f"[UPLOAD] File service type: {type(file_service)}")
        
        try:
            song = file_service.load_audio_file(temp_path)
            print(f"[UPLOAD] Song loaded successfully:")
            print(f"[UPLOAD]   - ID: {song.id}")
            print(f"[UPLOAD]   - Title: {song.title}")
            print(f"[UPLOAD]   - Artist: {song.artist}")
            print(f"[UPLOAD]   - Duration: {song.duration}")
            print(f"[UPLOAD]   - File path: {song.file_path}")
            print(f"[UPLOAD]   - Format: {song.format}")
        except Exception as e:
            print(f"[UPLOAD] ERROR loading song: {e}")
            import traceback
            traceback.print_exc()
            raise

        # PASO 6: Actualizar metadata si se proporciona
        if title or artist or album or year:
            print(f"[UPLOAD] Updating metadata...")
            metadata_updates = {}
            if title: metadata_updates['title'] = title.strip()
            if artist: metadata_updates['artist'] = artist.strip()
            if album: metadata_updates['album'] = album.strip()
            if year: metadata_updates['year'] = year
            
            print(f"[UPLOAD] Metadata updates: {metadata_updates}")
            
            try:
                song.update_metadata(**metadata_updates)
                print(f"[UPLOAD] Song metadata updated successfully")
                print(f"[UPLOAD] New title: {song.title}")
                print(f"[UPLOAD] New artist: {song.artist}")
            except Exception as e:
                print(f"[UPLOAD] ERROR updating song metadata: {e}")
            
            try:
                metadata_service.update_multiple_fields(temp_path, metadata_updates)
                print(f"[UPLOAD] File metadata updated successfully")
            except Exception as e:
                print(f"[UPLOAD] Warning: Could not update file metadata: {e}")

        # PASO 7: Añadir a playlist - CON LOGS DETALLADOS
        print(f"[UPLOAD] ===== ADDING SONG TO PLAYLIST =====")
        print(f"[UPLOAD] Playlist service memory address: {id(playlist_service)}")
        print(f"[UPLOAD] Playlist service type: {type(playlist_service)}")
        print(f"[UPLOAD] Number of playlists in service: {len(playlist_service.playlists)}")
        
        # Verificar que el servicio aún tiene la playlist
        service_playlist = playlist_service.get_playlist_by_id(playlist_id)
        if service_playlist:
            print(f"[UPLOAD] Service playlist found: {service_playlist.name}")
            print(f"[UPLOAD] Service playlist songs count: {service_playlist.song_count}")
            print(f"[UPLOAD] Service playlist memory address: {id(service_playlist)}")
        else:
            print(f"[UPLOAD] ERROR: Service playlist NOT FOUND")
            print(f"[UPLOAD] Available IDs: {[p.id for p in playlist_service.playlists]}")
        
        print(f"[UPLOAD] Song object to add:")
        print(f"[UPLOAD]   - Type: {type(song)}")
        print(f"[UPLOAD]   - ID: {song.id}")
        print(f"[UPLOAD]   - Title: {song.title}")
        print(f"[UPLOAD]   - Valid file: {song.is_valid_file()}")
        
        print(f"[UPLOAD] Calling playlist_service.add_song_to_playlist...")
        success = playlist_service.add_song_to_playlist(playlist_id, song)
        print(f"[UPLOAD] add_song_to_playlist returned: {success}")

        if not success:
            print(f"[UPLOAD] ===== CRITICAL ERROR: Failed to add song to playlist =====")
            print(f"[UPLOAD] Service state after failure:")
            print(f"[UPLOAD]   - Service has {len(playlist_service.playlists)} playlists")
            print(f"[UPLOAD]   - Available playlist IDs: {[p.id for p in playlist_service.playlists]}")
            
            # Verificar el estado de la playlist específica
            failed_playlist = playlist_service.get_playlist_by_id(playlist_id)
            if failed_playlist:
                print(f"[UPLOAD]   - Failed playlist still exists: {failed_playlist.name}")
                print(f"[UPLOAD]   - Failed playlist songs: {failed_playlist.song_count}")
            else:
                print(f"[UPLOAD]   - Failed playlist no longer exists in service")
            
            # Limpiar archivo
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"[UPLOAD] Cleaned up temp file: {temp_path}")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add song to playlist"
            )
        
        print(f"[UPLOAD] ===== SUCCESS: Song added to playlist =====")
        
        # Verificar el estado final
        final_playlist = playlist_service.get_playlist_by_id(playlist_id)
        if final_playlist:
            print(f"[UPLOAD] Final playlist state:")
            print(f"[UPLOAD]   - Name: {final_playlist.name}")
            print(f"[UPLOAD]   - Songs count: {final_playlist.song_count}")
            print(f"[UPLOAD]   - Last song: {final_playlist.get_songs_list()[-1].title if final_playlist.get_songs_list() else 'None'}")

        print(f"[UPLOAD] ===== UPLOAD COMPLETED SUCCESSFULLY =====")

        return {
            "message": "Song uploaded and added to playlist successfully",
            "song_id": song.id,
            "playlist_id": playlist_id,
            "song": {
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "duration": song.duration,
                "duration_formatted": song.get_duration_formatted(),
                "format": song.format,
                "filename": song.filename
            }
        }

    except HTTPException:
        print(f"[UPLOAD] HTTPException occurred, re-raising...")
        raise
    except Exception as e:
        print(f"[UPLOAD] ===== UNEXPECTED ERROR =====")
        print(f"[UPLOAD] Error type: {type(e)}")
        print(f"[UPLOAD] Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Limpiar archivo en caso de error
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"[UPLOAD] Cleaned up temp file: {temp_path}")
            except:
                print(f"[UPLOAD] Failed to clean up temp file: {temp_path}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.delete("/{playlist_id}/songs/{song_id}")
async def remove_song_from_playlist(
    song_id: str = Depends(validate_song_id),
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Remove a song from a playlist.
    
    Removes the specified song from the playlist and updates positions.
    """
    try:
        success = playlist_service.remove_song_from_playlist(playlist_id, song_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found in playlist"
            )
        
        return {
            "message": "Song removed from playlist successfully",
            "song_id": song_id,
            "playlist_id": playlist_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing song from playlist: {str(e)}"
        )


@router.put("/{playlist_id}/songs/reorder")
async def reorder_songs(
    request: ReorderRequest,
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Reorder songs in a playlist.
    
    Moves a song from one position to another using the DoublyLinkedList structure.
    """
    try:
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(str(playlist_id))
        
        # Validate positions
        if (request.from_position < 0 or request.from_position >= playlist.song_count or
            request.to_position < 0 or request.to_position >= playlist.song_count):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid positions. Must be between 0 and {playlist.song_count - 1}"
            )
        
        if request.from_position == request.to_position:
            return {
                "message": "No change needed",
                "from_position": request.from_position,
                "to_position": request.to_position
            }
        
        # Perform reorder using DoublyLinkedList move operation
        success = playlist_service.move_song_in_playlist(
            playlist_id=playlist_id,
            from_pos=request.from_position,
            to_pos=request.to_position
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reorder songs"
            )
        
        return {
            "message": "Songs reordered successfully",
            "from_position": request.from_position,
            "to_position": request.to_position
        }
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reordering songs: {str(e)}"
        )


@router.post("/{playlist_id}/shuffle")
async def shuffle_playlist(
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Shuffle songs in a playlist.
    
    Randomly reorders all songs in the playlist using the DoublyLinkedList shuffle method.
    """
    try:
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(str(playlist_id))
        
        if playlist.song_count <= 1:
            return {
                "message": "Playlist has too few songs to shuffle",
                "song_count": playlist.song_count
            }
        
        success = playlist_service.shuffle_playlist(playlist_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to shuffle playlist"
            )
        
        return {
            "message": "Playlist shuffled successfully",
            "playlist_id": playlist_id,
            "song_count": playlist.song_count
        }
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error shuffling playlist: {str(e)}"
        )


# ADDITIONAL FEATURES

@router.get("/search", response_model=PlaylistSearchResponse)
async def search_playlists(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Search playlists by name or description.
    
    Returns paginated search results.
    """
    try:
        query = validate_search_query(q)
        page, limit = validate_pagination(page, limit)
        
        # Search playlists
        results = playlist_service.search_playlists(query)
        total_count = len(results)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = results[start_idx:end_idx]
        
        # Convert to response models
        response_playlists = [
            PlaylistResponse(
                id=playlist.id,
                name=playlist.name,
                description=playlist.description,
                cover_image=playlist.cover_image,
                song_count=playlist.song_count,
                total_duration=playlist.total_duration,
                total_duration_formatted=playlist.get_total_duration_formatted(),
                created_at=playlist.created_at.isoformat()
            )
            for playlist in paginated_results
        ]
        
        return PlaylistSearchResponse(
            playlists=response_playlists,
            total_count=total_count,
            page=page,
            limit=limit,
            has_next=end_idx < total_count,
            has_previous=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching playlists: {str(e)}"
        )


@router.post("/{playlist_id}/duplicate", response_model=PlaylistResponse)
async def duplicate_playlist(
    new_name: Optional[str] = Form(None, description="Name for the duplicated playlist"),
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Create a duplicate of an existing playlist.
    
    Creates a copy of the playlist with all its songs and metadata.
    """
    try:
        duplicated_playlist = playlist_service.duplicate_playlist(playlist_id, new_name)
        
        if not duplicated_playlist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to duplicate playlist"
            )
        
        return PlaylistResponse(
            id=duplicated_playlist.id,
            name=duplicated_playlist.name,
            description=duplicated_playlist.description,
            cover_image=duplicated_playlist.cover_image,
            song_count=duplicated_playlist.song_count,
            total_duration=duplicated_playlist.total_duration,
            total_duration_formatted=duplicated_playlist.get_total_duration_formatted(),
            created_at=duplicated_playlist.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error duplicating playlist: {str(e)}"
        )


@router.get("/{playlist_id}/export", response_model=ExportResponse)
async def export_playlist(
    export_format: str = Query("json", description="Export format (json, m3u, txt)"),
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Export playlist data in various formats.
    
    Supports JSON, M3U, and text formats for playlist export.
    """
    try:
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(str(playlist_id))
        
        export_format = export_format.lower()
        if export_format not in ["json", "m3u", "txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export format. Supported: json, m3u, txt"
            )
        
        songs_list = playlist.get_songs_list()
        
        # Prepare song data for export
        export_songs = []
        for idx, song in enumerate(songs_list):
            song_data = {
                "position": idx + 1,
                "title": song.title,
                "artist": song.artist,
                "album": song.album,
                "duration": song.duration,
                "file_path": song.file_path,
                "format": song.format
            }
            
            if export_format == "m3u":
                song_data["extinf"] = f"#EXTINF:{int(song.duration)},{song.get_display_name()}"
            
            export_songs.append(song_data)
        
        return ExportResponse(
            playlist_name=playlist.name,
            export_format=export_format,
            songs=export_songs,
            total_songs=len(export_songs),
            total_duration=playlist.total_duration
        )
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting playlist: {str(e)}"
        )
    

    # Agrega este endpoint en playlists.py (después del endpoint POST de crear playlist):

@router.put("/{playlist_id}")
async def update_playlist(
    playlist_data: PlaylistUpdate,
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Update playlist information.
    
    Updates name and description of an existing playlist.
    """
    try:
        print(f"[UPDATE] ===== UPDATING PLAYLIST =====")
        print(f"[UPDATE] Playlist ID: {playlist_id}")
        print(f"[UPDATE] New name: {playlist_data.name}")
        print(f"[UPDATE] New description: {playlist_data.description}")
        
        # Verificar que al menos un campo esté presente
        if not playlist_data.name and not playlist_data.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field (name or description) must be provided"
            )
        
        # Obtener playlist actual para conservar valores no actualizados
        current_playlist = playlist_service.get_playlist_by_id(playlist_id)
        if not current_playlist:
            raise PlaylistNotFoundError(playlist_id)
        
        # Usar valores actuales si no se proporcionan nuevos
        update_name = playlist_data.name if playlist_data.name else current_playlist.name
        update_description = playlist_data.description if playlist_data.description is not None else current_playlist.description
        
        print(f"[UPDATE] Final name: {update_name}")
        print(f"[UPDATE] Final description: {update_description}")
        
        success = playlist_service.update_playlist(
            playlist_id=playlist_id,
            name=update_name,
            description=update_description or ""
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update playlist"
            )
        
        # Obtener playlist actualizada
        updated_playlist = playlist_service.get_playlist_by_id(playlist_id)
        
        return PlaylistResponse(
            id=updated_playlist.id,
            name=updated_playlist.name,
            description=updated_playlist.description,
            cover_image=updated_playlist.cover_image,
            song_count=updated_playlist.song_count,
            total_duration=updated_playlist.total_duration,
            total_duration_formatted=updated_playlist.get_total_duration_formatted(),
            created_at=updated_playlist.created_at.isoformat()
        )
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        print(f"[UPDATE] Error updating playlist: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating playlist: {str(e)}"
        )


# En playlists.py, asegúrate de que este endpoint esté presente y funcionando:

@router.put("/{playlist_id}/cover")
async def update_playlist_cover(
    cover_file: UploadFile = File(..., description="Cover image file"),
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    file_service: FileService = Depends(get_file_service)
):
    """Update cover image for a playlist."""
    try:
        print(f"[COVER] Updating cover for playlist: {playlist_id}")
        
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if not playlist:
            raise PlaylistNotFoundError(playlist_id)
        
        if not cover_file.filename:
            raise HTTPException(status_code=400, detail="No cover image provided")
        
        # Leer imagen
        image_data = await cover_file.read()
        print(f"[COVER] Image data read: {len(image_data)} bytes")
        
        file_extension = os.path.splitext(cover_file.filename)[1].lower()
        if not file_extension:
            file_extension = '.jpg'
        
        # Guardar imagen físicamente
        cover_path = file_service.save_cover_image(
            f"playlist_{playlist.id}", 
            image_data, 
            file_extension.lstrip('.')
        )
        print(f"[COVER] Cover saved to: {cover_path}")
        
        # CRÍTICO: Guardar URL del endpoint, NO el path físico
        playlist.cover_image = f"/api/playlists/{playlist.id}/cover-image"
        
        save_success = playlist_service.save_playlists_to_file()
        print(f"[COVER] Playlist saved: {save_success}")
        
        return {
            "message": "Playlist cover updated successfully",
            "cover_url": playlist.cover_image,
            "playlist_id": playlist.id
        }
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        print(f"[COVER] Error updating cover: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating cover: {str(e)}")


# UTILITY ENDPOINTS

@router.get("/stats")
async def get_playlists_stats(
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get statistics about playlists in the system.
    
    Returns counts and aggregated information.
    """
    try:
        playlists = playlist_service.get_all_playlists()
        
        total_playlists = len(playlists)
        total_songs = sum(playlist.song_count for playlist in playlists)
        total_duration = sum(playlist.total_duration for playlist in playlists)
        
        # Find largest and smallest playlists
        largest_playlist = max(playlists, key=lambda p: p.song_count) if playlists else None
        smallest_playlist = min(playlists, key=lambda p: p.song_count) if playlists else None
        
        # Calculate averages
        avg_songs_per_playlist = total_songs / total_playlists if total_playlists > 0 else 0
        avg_duration_per_playlist = total_duration / total_playlists if total_playlists > 0 else 0
        
        return {
            "total_playlists": total_playlists,
            "total_songs_across_playlists": total_songs,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": f"{int(total_duration // 3600):02d}:{int((total_duration % 3600) // 60):02d}:{int(total_duration % 60):02d}",
            "average_songs_per_playlist": round(avg_songs_per_playlist, 2),
            "average_duration_per_playlist_seconds": round(avg_duration_per_playlist, 2),
            "largest_playlist": {
                "name": largest_playlist.name,
                "song_count": largest_playlist.song_count
            } if largest_playlist else None,
            "smallest_playlist": {
                "name": smallest_playlist.name,
                "song_count": smallest_playlist.song_count
            } if smallest_playlist else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating playlist stats: {str(e)}"
        )


@router.post("/{playlist_id}/validate")
async def validate_playlist_files(
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Validate that all songs in a playlist still exist and are accessible.
    
    Returns validation results and can optionally clean up invalid songs.
    """
    try:
        validation_result = playlist_service.validate_playlist_songs(playlist_id)
        
        return {
            "playlist_id": playlist_id,
            "validation_result": validation_result,
            "cleanup_available": len(validation_result.get("invalid_songs", [])) > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating playlist: {str(e)}"
        )


@router.post("/{playlist_id}/cleanup")
async def cleanup_invalid_songs(
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Remove invalid songs from a playlist.
    
    Removes songs whose files no longer exist or are inaccessible.
    """
    try:
        removed_count = playlist_service.cleanup_invalid_songs(playlist_id)
        
        return {
            "message": "Playlist cleanup completed",
            "playlist_id": playlist_id,
            "songs_removed": removed_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up playlist: {str(e)}"
        )
    # Agrega este endpoint en playlists.py para servir las imágenes:

@router.get("/{playlist_id}/cover-image")
async def get_playlist_cover_image(
    playlist_id: str = Depends(validate_playlist_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """Get cover image file for a playlist."""
    try:
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if not playlist:
            raise PlaylistNotFoundError(playlist_id)
        
        # CRÍTICO: Si cover_image es URL relativa, construir path físico
        if playlist.cover_image:
            # Si ya tiene la ruta física, usar directamente
            if os.path.exists(playlist.cover_image):
                cover_path = playlist.cover_image
            else:
                # Si es URL relativa, construir path
                cover_path = os.path.join("frontend/static/uploads/covers", f"cover_playlist_{playlist.id}.jpg")
        else:
            raise HTTPException(status_code=404, detail="Cover image not found")
        
        if not os.path.exists(cover_path):
            raise HTTPException(status_code=404, detail="Cover image file not found")
        
        print(f"[COVER] Serving image: {cover_path}")
        
        return FileResponse(
            cover_path,
            media_type="image/jpeg",
            filename=f"playlist_cover_{playlist.id}.jpg"
        )
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        print(f"[COVER] Error serving image: {e}")
        raise HTTPException(status_code=500, detail="Error serving cover image")
    

