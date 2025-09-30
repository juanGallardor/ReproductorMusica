import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator

from models.song import Song
from services.playlist_service import PlaylistService
from services.file_service import FileService
from services.metadata_service import MetadataService
from api.dependencies import (
    get_playlist_service,
    get_file_service,
    get_metadata_service,
    validate_song_id,
    validate_audio_format,
    validate_search_query,
    validate_pagination,
    get_upload_directory,
    get_supported_formats,
    get_max_file_size,
    get_allowed_image_formats,
    SongNotFoundError,
    InvalidAudioFormatError,
    FileNotFoundError
)

# Create router
router = APIRouter(prefix="/songs", tags=["songs"])


# PYDANTIC MODELS

class SongBase(BaseModel):
    """Base song model with common fields."""
    title: str = Field(..., min_length=1, max_length=200, description="Song title")
    artist: Optional[str] = Field(None, max_length=100, description="Artist name")
    album: Optional[str] = Field(None, max_length=100, description="Album name")
    year: Optional[int] = Field(None, ge=1800, le=2100, description="Release year")
    
    @validator('title', 'artist', 'album')
    def strip_whitespace(cls, v):
        return v.strip() if v else v


class SongCreate(SongBase):
    """Model for creating a new song."""
    file_path: str = Field(..., description="Path to audio file")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class SongUpdate(BaseModel):
    """Model for updating song metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    artist: Optional[str] = Field(None, max_length=100)
    album: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1800, le=2100)
    
    @validator('title', 'artist', 'album')
    def strip_whitespace(cls, v):
        return v.strip() if v else v


class SongResponse(BaseModel):
    """Model for song response."""
    id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    year: Optional[int]
    duration: float
    file_size: int
    format: str
    filename: str
    play_count: int
    cover_image: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class SongDetailResponse(SongResponse):
    """Detailed song response with additional metadata."""
    file_path: str
    duration_formatted: str
    file_size_formatted: str
    display_name: str


class MetadataResponse(BaseModel):
    """Model for complete metadata response."""
    basic_info: Dict[str, Any]
    technical_info: Dict[str, Any]
    has_cover_art: bool
    cover_art_info: Optional[Dict[str, Any]] = None


class SongSearchResponse(BaseModel):
    """Model for search results."""
    songs: List[SongResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool


class DirectoryScanResponse(BaseModel):
    """Model for directory scan results."""
    found_files: List[str]
    loaded_songs: List[SongResponse]
    failed_files: List[str]
    total_found: int
    total_loaded: int


class UploadResponse(BaseModel):
    """Model for file upload response."""
    song: SongResponse
    message: str


# MAIN ENDPOINTS

@router.get("/", response_model=List[SongResponse])
async def list_songs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get list of all songs from all playlists.
    
    Returns paginated list of songs with basic information.
    """
    try:
        # Validate pagination
        page, limit = validate_pagination(page, limit)
        
        # Get all songs from all playlists
        all_songs = []
        playlists = playlist_service.get_all_playlists()
        
        for playlist in playlists:
            all_songs.extend(playlist.get_songs_list())
        
        # Remove duplicates by ID
        unique_songs = {}
        for song in all_songs:
            if song.id not in unique_songs:
                unique_songs[song.id] = song
        
        songs_list = list(unique_songs.values())
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_songs = songs_list[start_idx:end_idx]
        
        # Convert to response models
        response_songs = [
            SongResponse(
                id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                year=song.year,
                duration=song.duration,
                file_size=song.file_size,
                format=song.format,
                filename=song.filename,
                play_count=song.play_count,
                cover_image=song.cover_image,
                created_at=song.created_at.isoformat()
            )
            for song in paginated_songs
        ]
        
        return response_songs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving songs: {str(e)}"
        )


@router.get("/{song_id}", response_model=SongDetailResponse)
async def get_song(
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get detailed information about a specific song.
    
    Returns complete song information including formatted fields.
    """
    # Find song across all playlists
    song = None
    playlists = playlist_service.get_all_playlists()
    
    for playlist in playlists:
        found_song = playlist.find_song(song_id)
        if found_song:
            song = found_song
            break
    
    if not song:
        raise SongNotFoundError(song_id)
    
    return SongDetailResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        album=song.album,
        year=song.year,
        duration=song.duration,
        file_size=song.file_size,
        format=song.format,
        filename=song.filename,
        play_count=song.play_count,
        cover_image=song.cover_image,
        created_at=song.created_at.isoformat(),
        file_path=song.file_path,
        duration_formatted=song.get_duration_formatted(),
        file_size_formatted=song.get_file_size_formatted(),
        display_name=song.get_display_name()
    )


@router.get("/{song_id}/stream")
async def stream_song(
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Stream audio file for playback.
    Returns the actual audio file for HTML5 audio player.
    """
    # Find song
    song = None
    playlists = playlist_service.get_all_playlists()
    
    for playlist in playlists:
        found_song = playlist.find_song(song_id)
        if found_song:
            song = found_song
            break
    
    if not song:
        raise SongNotFoundError(song_id)
    
    if not song.is_valid_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return FileResponse(
        song.file_path,
        media_type=f"audio/{song.format}",
        filename=song.filename
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_song(
    file: UploadFile = File(..., description="Audio file to upload"),
    title: Optional[str] = Form(None, description="Custom title (optional)"),
    artist: Optional[str] = Form(None, description="Artist name (optional)"),
    album: Optional[str] = Form(None, description="Album name (optional)"),
    year: Optional[int] = Form(None, description="Release year (optional)"),
    file_service: FileService = Depends(get_file_service),
    metadata_service: MetadataService = Depends(get_metadata_service),
    upload_dir: str = Depends(get_upload_directory),
    max_file_size: int = Depends(get_max_file_size)
):
    """
    Upload a new audio file and create a song entry.
    
    Accepts audio files in supported formats and extracts metadata.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file size
    if file.size and file.size > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_file_size} bytes"
        )
    
    # Validate file format
    file_extension = os.path.splitext(file.filename)[1].lower()
    validate_audio_format(file_extension)
    
    try:
        # Save uploaded file
        clean_filename = file_service.clean_filename(file.filename)
        temp_path = os.path.join(upload_dir, clean_filename)
        
        # Handle duplicate filenames
        if os.path.exists(temp_path):
            base_name, ext = os.path.splitext(clean_filename)
            unique_filename = file_service.generate_unique_filename(base_name, ext)
            temp_path = os.path.join(upload_dir, unique_filename)
        
        # Write file to disk
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Load song using FileService
        song = file_service.load_audio_file(temp_path)
        
        # Override metadata if provided
        metadata_updates = {}
        if title:
            metadata_updates['title'] = title.strip()
        if artist:
            metadata_updates['artist'] = artist.strip()
        if album:
            metadata_updates['album'] = album.strip()
        if year:
            metadata_updates['year'] = year
        
        # Update metadata if provided
        if metadata_updates:
            song.update_metadata(**metadata_updates)
            
            # Also update in file if metadata service is available
            try:
                metadata_service.update_multiple_fields(temp_path, metadata_updates)
            except Exception as e:
                print(f"Warning: Could not update file metadata: {e}")
        
        # Convert to response
        response_song = SongResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
            album=song.album,
            year=song.year,
            duration=song.duration,
            file_size=song.file_size,
            format=song.format,
            filename=song.filename,
            play_count=song.play_count,
            cover_image=song.cover_image,
            created_at=song.created_at.isoformat()
        )
        
        return UploadResponse(
            song=response_song,
            message="Song uploaded successfully"
        )
        
    except Exception as e:
        # Clean up uploaded file on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading song: {str(e)}"
        )


@router.put("/{song_id}", response_model=SongDetailResponse)
async def update_song(
    song_data: SongUpdate,
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    metadata_service: MetadataService = Depends(get_metadata_service)
):
    """
    Update song metadata.
    
    Updates both the Song object and the file metadata.
    """
    # Find song
    song = None
    playlists = playlist_service.get_all_playlists()
    
    for playlist in playlists:
        found_song = playlist.find_song(song_id)
        if found_song:
            song = found_song
            break
    
    if not song:
        raise SongNotFoundError(song_id)
    
    try:
        # Prepare update data
        update_data = {}
        if song_data.title is not None:
            update_data['title'] = song_data.title
        if song_data.artist is not None:
            update_data['artist'] = song_data.artist
        if song_data.album is not None:
            update_data['album'] = song_data.album
        if song_data.year is not None:
            update_data['year'] = song_data.year
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update Song object
        song.update_metadata(**update_data)
        
        # Update file metadata
        try:
            metadata_service.update_multiple_fields(song.file_path, update_data)
        except Exception as e:
            print(f"Warning: Could not update file metadata: {e}")
        
        # Save playlists
        playlist_service.save_playlists_to_file()
        
        return SongDetailResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
            album=song.album,
            year=song.year,
            duration=song.duration,
            file_size=song.file_size,
            format=song.format,
            filename=song.filename,
            play_count=song.play_count,
            cover_image=song.cover_image,
            created_at=song.created_at.isoformat(),
            file_path=song.file_path,
            duration_formatted=song.get_duration_formatted(),
            file_size_formatted=song.get_file_size_formatted(),
            display_name=song.get_display_name()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating song: {str(e)}"
        )


@router.delete("/{song_id}")
async def delete_song(
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Delete a song from all playlists and optionally remove the file.
    
    This removes the song from all playlists but keeps the physical file.
    """
    song_found = False
    deleted_from_playlists = []
    
    # Remove song from all playlists
    playlists = playlist_service.get_all_playlists()
    for playlist in playlists:
        if playlist.remove_song(song_id):
            song_found = True
            deleted_from_playlists.append(playlist.name)
    
    if not song_found:
        raise SongNotFoundError(song_id)
    
    # Save updated playlists
    playlist_service.save_playlists_to_file()
    
    return {
        "message": "Song deleted successfully",
        "song_id": song_id,
        "removed_from_playlists": deleted_from_playlists
    }


# SEARCH AND DISCOVERY ENDPOINTS

@router.get("/search", response_model=SongSearchResponse)
async def search_songs(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Search songs by title, artist, or album.
    
    Returns paginated search results.
    """
    query = validate_search_query(q)
    page, limit = validate_pagination(page, limit)
    
    try:
        # Search across all playlists
        all_results = []
        playlists = playlist_service.get_all_playlists()
        
        for playlist in playlists:
            results = playlist_service.search_songs_in_playlist(playlist.id, query)
            all_results.extend(results)
        
        # Remove duplicates
        unique_results = {}
        for song in all_results:
            if song.id not in unique_results:
                unique_results[song.id] = song
        
        results_list = list(unique_results.values())
        total_count = len(results_list)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = results_list[start_idx:end_idx]
        
        # Convert to response models
        response_songs = [
            SongResponse(
                id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                year=song.year,
                duration=song.duration,
                file_size=song.file_size,
                format=song.format,
                filename=song.filename,
                play_count=song.play_count,
                cover_image=song.cover_image,
                created_at=song.created_at.isoformat()
            )
            for song in paginated_results
        ]
        
        return SongSearchResponse(
            songs=response_songs,
            total_count=total_count,
            page=page,
            limit=limit,
            has_next=end_idx < total_count,
            has_previous=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching songs: {str(e)}"
        )


@router.post("/scan-directory", response_model=DirectoryScanResponse)
async def scan_directory(
    directory_path: str = Form(..., description="Directory path to scan"),
    file_service: FileService = Depends(get_file_service)
):
    """
    Scan a directory for audio files and load them.
    
    Returns information about found and loaded files.
    """
    if not os.path.exists(directory_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory not found: {directory_path}"
        )
    
    if not os.path.isdir(directory_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a directory: {directory_path}"
        )
    
    try:
        # Scan directory for audio files
        found_files = file_service.scan_directory_for_audio(directory_path)
        
        # Load songs
        loaded_songs = []
        failed_files = []
        
        for file_path in found_files:
            try:
                song = file_service.load_audio_file(file_path)
                loaded_songs.append(song)
            except Exception as e:
                failed_files.append(f"{file_path}: {str(e)}")
        
        # Convert to response models
        response_songs = [
            SongResponse(
                id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                year=song.year,
                duration=song.duration,
                file_size=song.file_size,
                format=song.format,
                filename=song.filename,
                play_count=song.play_count,
                cover_image=song.cover_image,
                created_at=song.created_at.isoformat()
            )
            for song in loaded_songs
        ]
        
        return DirectoryScanResponse(
            found_files=found_files,
            loaded_songs=response_songs,
            failed_files=failed_files,
            total_found=len(found_files),
            total_loaded=len(loaded_songs)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning directory: {str(e)}"
        )


# METADATA ENDPOINTS

@router.get("/{song_id}/metadata", response_model=MetadataResponse)
async def get_song_metadata(
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    metadata_service: MetadataService = Depends(get_metadata_service)
):
    """
    Get complete metadata information for a song.
    
    Returns both basic and technical metadata extracted from the file.
    """
    # Find song
    song = None
    playlists = playlist_service.get_all_playlists()
    
    for playlist in playlists:
        found_song = playlist.find_song(song_id)
        if found_song:
            song = found_song
            break
    
    if not song:
        raise SongNotFoundError(song_id)
    
    try:
        # Extract complete metadata
        complete_metadata = metadata_service.extract_metadata(song.file_path)
        basic_info = metadata_service.get_basic_info(song.file_path)
        technical_info = metadata_service.get_technical_info(song.file_path)
        cover_art_info = metadata_service.get_cover_art_info(song.file_path)
        
        return MetadataResponse(
            basic_info=basic_info,
            technical_info=technical_info,
            has_cover_art=cover_art_info.get('has_cover', False),
            cover_art_info=cover_art_info if cover_art_info.get('has_cover') else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting metadata: {str(e)}"
        )


@router.put("/{song_id}/cover")
async def update_song_cover(
    cover_file: UploadFile = File(..., description="Cover image file"),
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    metadata_service: MetadataService = Depends(get_metadata_service),
    file_service: FileService = Depends(get_file_service),
    allowed_formats: List[str] = Depends(get_allowed_image_formats)
):
    """
    Update cover art for a song.
    
    Accepts image files and embeds them into the audio file.
    """
    # Find song
    song = None
    playlists = playlist_service.get_all_playlists()
    
    for playlist in playlists:
        found_song = playlist.find_song(song_id)
        if found_song:
            song = found_song
            break
    
    if not song:
        raise SongNotFoundError(song_id)
    
    # Validate image file
    if not cover_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No cover image provided"
        )
    
    file_extension = os.path.splitext(cover_file.filename)[1].lower()
    if file_extension not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format. Allowed: {', '.join(allowed_formats)}"
        )
    
    try:
        # Read image data
        image_data = await cover_file.read()
        
        # Determine MIME type
        mime_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_type_map.get(file_extension, 'image/jpeg')
        
        # Save cover image
        cover_path = file_service.save_cover_image(song.id, image_data, file_extension.lstrip('.'))
        
        # Embed in audio file
        embed_success = metadata_service.embed_cover_art(song.file_path, image_data, mime_type)
        
        # Update song cover path
        song.cover_image = cover_path
        playlist_service.save_playlists_to_file()
        
        return {
            "message": "Cover art updated successfully",
            "cover_path": cover_path,
            "embedded_in_file": embed_success
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating cover art: {str(e)}"
        )


@router.get("/{song_id}/cover")
async def get_song_cover(
    song_id: str = Depends(validate_song_id),
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get cover art file for a song.
    
    Returns the cover image file if available.
    """
    # Find song
    song = None
    playlists = playlist_service.get_all_playlists()
    
    for playlist in playlists:
        found_song = playlist.find_song(song_id)
        if found_song:
            song = found_song
            break
    
    if not song:
        raise SongNotFoundError(song_id)
    
    if not song.cover_image or not os.path.exists(song.cover_image):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover art not found"
        )
    
    return FileResponse(
        song.cover_image,
        media_type="image/jpeg",
        filename=f"cover_{song.id}.jpg"
    )


# UTILITY ENDPOINTS

@router.get("/formats/supported")
async def get_supported_formats_endpoint(
    supported_formats: List[str] = Depends(get_supported_formats)
):
    """
    Get list of supported audio formats.
    
    Returns information about supported file formats and limitations.
    """
    return {
        "supported_formats": supported_formats,
        "max_file_size": get_max_file_size(),
        "allowed_image_formats": get_allowed_image_formats()
    }


@router.get("/stats")
async def get_songs_stats(
    playlist_service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get statistics about songs in the system.
    
    Returns counts and aggregated information.
    """
    try:
        playlists = playlist_service.get_all_playlists()
        
        # Collect all unique songs
        unique_songs = {}
        total_duration = 0
        total_size = 0
        format_counts = {}
        
        for playlist in playlists:
            for song in playlist.get_songs_list():
                if song.id not in unique_songs:
                    unique_songs[song.id] = song
                    total_duration += song.duration
                    total_size += song.file_size
                    
                    format_key = song.format.lower()
                    format_counts[format_key] = format_counts.get(format_key, 0) + 1
        
        return {
            "total_songs": len(unique_songs),
            "total_duration_seconds": total_duration,
            "total_duration_formatted": f"{int(total_duration // 3600):02d}:{int((total_duration % 3600) // 60):02d}:{int(total_duration % 60):02d}",
            "total_size_bytes": total_size,
            "total_size_formatted": f"{total_size / (1024*1024*1024):.2f} GB",
            "format_distribution": format_counts,
            "average_song_duration": total_duration / len(unique_songs) if unique_songs else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating stats: {str(e)}"
        )
                                      