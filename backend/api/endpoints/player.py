from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, validator

from patterns.singleton import MusicPlayerManager
from services.audio_service import AudioService
from services.playlist_service import PlaylistService
from models.song import Song
from api.dependencies import (
    get_music_player_manager,
    get_audio_service,
    get_playlist_service,
    validate_playlist_id,
    validate_volume_level,
    PlaylistNotFoundError
)

# Create router
router = APIRouter(prefix="/player", tags=["player"])


# PYDANTIC MODELS

class VolumeUpdate(BaseModel):
    """Model for volume update requests."""
    volume: float = Field(..., ge=0, le=100, description="Volume level (0-100)")
    
    @validator('volume')
    def validate_volume(cls, v):
        return validate_volume_level(v)


class SeekPosition(BaseModel):
    """Model for seek position requests."""
    position: float = Field(..., ge=0, description="Position in seconds")


class RepeatModeUpdate(BaseModel):
    """Model for repeat mode update."""
    mode: str = Field(..., description="Repeat mode: off, one, all")
    
    @validator('mode')
    def validate_repeat_mode(cls, v):
        if v not in ['off', 'one', 'all']:
            raise ValueError("Repeat mode must be 'off', 'one', or 'all'")
        return v


class ShuffleUpdate(BaseModel):
    """Model for shuffle mode update."""
    enabled: bool = Field(..., description="Enable or disable shuffle mode")


class SkipRequest(BaseModel):
    """Model for skip forward/backward requests."""
    seconds: int = Field(default=10, ge=1, le=60, description="Seconds to skip (1-60)")


class CurrentSongResponse(BaseModel):
    """Model for current song response."""
    id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    year: Optional[int]
    duration: float
    duration_formatted: str
    format: str
    filename: str
    display_name: str
    cover_image: Optional[str]
    position_in_playlist: int


class PlaylistInfo(BaseModel):
    """Model for current playlist information."""
    id: str
    name: str
    song_count: int
    current_position: int
    has_next: bool
    has_previous: bool


class PlayerStatus(BaseModel):
    is_playing: bool
    is_paused: bool
    volume: float
    repeat_mode: str
    shuffle_mode: bool
    position_seconds: float
    position_formatted: str
    current_song: Optional[CurrentSongResponse] = None  
    current_playlist: Optional[PlaylistInfo] = None     
    has_audio_loaded: bool


class PlayerControls(BaseModel):
    """Model for available player controls."""
    can_play: bool
    can_pause: bool
    can_stop: bool
    can_next: bool
    can_previous: bool
    can_seek: bool


# CONTROL ENDPOINTS
@router.post("/play")
async def play(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    audio_service: AudioService = Depends(get_audio_service)
):
    """Start or resume playback of the current song."""
    try:
        if not player_manager.current_playlist or player_manager.current_playlist.is_empty():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No playlist or songs available for playback"
            )
        
        current_song = player_manager.current_playlist.get_current_song()
        if not current_song:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No current song selected"
            )
        
        print(f"[PLAYER] Play request for: {current_song.title}")
        
        # CRÍTICO: Verificar si necesitamos cargar nueva canción
        loaded_song = audio_service.get_current_song()
        
        if not loaded_song or loaded_song.id != current_song.id:
            # Es una canción diferente - cargar nueva
            print(f"[PLAYER] Loading new song: {current_song.title}")
            success = audio_service.load_song(current_song)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to load song for playback"
                )
        
        # Reproducir (cargar o reanudar)
        success = audio_service.play()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start playback"
            )
        
        # Incrementar contador de reproducción
        current_song.increment_play_count()
        
        print(f"[PLAYER] Successfully playing: {current_song.title}")
        
        return {
            "message": "Playback started",
            "song": current_song.get_display_name(),
            "is_playing": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PLAYER] Error starting playback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting playback: {str(e)}"
        )

@router.post("/pause")
async def pause(
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Pause the current playback.
    
    Pauses playback while maintaining the current position.
    """
    try:
        if not audio_service.is_playing():
            return {
                "message": "Playback is not active",
                "is_paused": audio_service.is_paused()
            }
        
        success = audio_service.pause()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to pause playback"
            )
        
        return {
            "message": "Playback paused",
            "is_paused": True,
            "position": audio_service.get_position()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing playback: {str(e)}"
        )


@router.post("/stop")
async def stop(
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Stop playback and reset position to beginning.
    
    Completely stops playback and resets position to 0.
    """
    try:
        success = audio_service.stop()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop playback"
            )
        
        return {
            "message": "Playback stopped",
            "is_playing": False,
            "position": 0.0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping playback: {str(e)}"
        )


@router.post("/next")
async def next_song(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Skip to the next song in the playlist.
    
    Advances to the next song using DoublyLinkedList navigation.
    """
    try:
        if not player_manager.current_playlist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active playlist"
            )
        
        was_playing = audio_service.is_playing()
        
        # Use player manager's next song logic (handles repeat modes)
        success = player_manager.next_song()
        
        if not success:
            return {
                "message": "No next song available",
                "at_end": True
            }
        
        # Load and play the new song if we were playing
        current_song = player_manager.current_playlist.get_current_song()
        if current_song:
            audio_service.load_song(current_song)
            if was_playing:
                audio_service.play()
        
        return {
            "message": "Moved to next song",
            "song": current_song.get_display_name() if current_song else None,
            "position": player_manager.current_playlist.current_position,
            "is_playing": was_playing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error moving to next song: {str(e)}"
        )


@router.post("/previous")
async def previous_song(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Skip to the previous song in the playlist.
    
    Goes back to the previous song using DoublyLinkedList navigation.
    """
    try:
        if not player_manager.current_playlist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active playlist"
            )
        
        was_playing = audio_service.is_playing()
        
        # Use player manager's previous song logic
        success = player_manager.previous_song()
        
        if not success:
            return {
                "message": "No previous song available",
                "at_beginning": True
            }
        
        # Load and play the new song if we were playing
        current_song = player_manager.current_playlist.get_current_song()
        if current_song:
            audio_service.load_song(current_song)
            if was_playing:
                audio_service.play()
        
        return {
            "message": "Moved to previous song",
            "song": current_song.get_display_name() if current_song else None,
            "position": player_manager.current_playlist.current_position,
            "is_playing": was_playing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error moving to previous song: {str(e)}"
        )


# CONFIGURATION ENDPOINTS

@router.put("/volume")
async def set_volume(
    volume_data: VolumeUpdate,
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Set the playback volume.
    
    Updates the volume level for audio playback (0-100).
    """
    try:
        success = audio_service.set_volume(volume_data.volume)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set volume"
            )
        
        return {
            "message": "Volume updated",
            "volume": volume_data.volume
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting volume: {str(e)}"
        )


@router.put("/seek")
async def seek_position(
    seek_data: SeekPosition,
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Seek to a specific position in the current song.
    
    Jumps to the specified position in seconds.
    """
    try:
        if not audio_service.is_song_loaded():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No song loaded for seeking"
            )
        
        current_song = audio_service.get_current_song()
        if seek_data.position > current_song.duration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Position exceeds song duration ({current_song.duration} seconds)"
            )
        
        success = audio_service.seek(seek_data.position)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to seek to position"
            )
        
        return {
            "message": "Seek completed",
            "position": seek_data.position,
            "duration": current_song.duration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error seeking: {str(e)}"
        )


@router.put("/repeat-mode")
async def set_repeat_mode(
    repeat_data: RepeatModeUpdate,
    player_manager: MusicPlayerManager = Depends(get_music_player_manager)
):
    """Set the repeat mode for playback."""
    try:
        print(f"[PLAYER] Setting repeat mode to: {repeat_data.mode}")
        player_manager.set_repeat_mode(repeat_data.mode)
        
        return {
            "message": "Repeat mode updated",
            "repeat_mode": repeat_data.mode
        }
        
    except Exception as e:
        print(f"[PLAYER] Error setting repeat mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting repeat mode: {str(e)}"
        )



@router.put("/shuffle-mode")
async def set_shuffle_mode(
    shuffle_data: ShuffleUpdate,
    player_manager: MusicPlayerManager = Depends(get_music_player_manager)
):
    """
    Enable or disable shuffle mode.
    
    When enabled, songs in the current playlist are shuffled.
    """
    try:
        player_manager.set_shuffle_mode(shuffle_data.enabled)
        
        return {
            "message": f"Shuffle mode {'enabled' if shuffle_data.enabled else 'disabled'}",
            "shuffle_mode": shuffle_data.enabled
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting shuffle mode: {str(e)}"
        )


# STATE ENDPOINTS

@router.get("/status", response_model=PlayerStatus)
async def get_player_status(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Get complete player status.
    
    Returns comprehensive information about the current player state.
    """
    try:
        current_song = None
        current_playlist_info = None
        
        # Get current song info
        if player_manager.current_playlist and not player_manager.current_playlist.is_empty():
            song = player_manager.current_playlist.get_current_song()
            if song:
                current_song = CurrentSongResponse(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    year=song.year,
                    duration=song.duration,
                    duration_formatted=song.get_duration_formatted(),
                    format=song.format,
                    filename=song.filename,
                    display_name=song.get_display_name(),
                    cover_image=song.cover_image,
                    position_in_playlist=player_manager.current_playlist.current_position
                )
        
        # Get playlist info
        if player_manager.current_playlist:
            current_playlist_info = PlaylistInfo(
                id=player_manager.current_playlist.id,
                name=player_manager.current_playlist.name,
                song_count=player_manager.current_playlist.song_count,
                current_position=player_manager.current_playlist.current_position,
                has_next=player_manager.current_playlist.has_next(),
                has_previous=player_manager.current_playlist.has_previous()
            )
        
        # Format current position
        position_seconds = audio_service.get_position()
        position_formatted = f"{int(position_seconds // 60):02d}:{int(position_seconds % 60):02d}"
        
        return PlayerStatus(
            is_playing=audio_service.is_playing(),
            is_paused=audio_service.is_paused(),
            volume=audio_service.get_volume(),
            repeat_mode=player_manager.repeat_mode,
            shuffle_mode=player_manager.shuffle_mode,
            position_seconds=position_seconds,
            position_formatted=position_formatted,
            current_song=current_song,
            current_playlist=current_playlist_info,
            has_audio_loaded=audio_service.is_song_loaded()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting player status: {str(e)}"
        )


@router.get("/current-song", response_model=Optional[CurrentSongResponse])
async def get_current_song(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager)
):
    """
    Get information about the currently selected song.
    
    Returns detailed information about the current song or null if none.
    """
    try:
        if not player_manager.current_playlist or player_manager.current_playlist.is_empty():
            return None
        
        song = player_manager.current_playlist.get_current_song()
        if not song:
            return None
        
        return CurrentSongResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
            album=song.album,
            year=song.year,
            duration=song.duration,
            duration_formatted=song.get_duration_formatted(),
            format=song.format,
            filename=song.filename,
            display_name=song.get_display_name(),
            cover_image=song.cover_image,
            position_in_playlist=player_manager.current_playlist.current_position
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting current song: {str(e)}"
        )


@router.get("/position")
async def get_position(
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Get current playback position.
    
    Returns the current position in seconds and formatted time.
    """
    try:
        position_seconds = audio_service.get_position()
        position_formatted = f"{int(position_seconds // 60):02d}:{int(position_seconds % 60):02d}"
        
        current_song = audio_service.get_current_song()
        duration = current_song.duration if current_song else 0
        
        return {
            "position_seconds": position_seconds,
            "position_formatted": position_formatted,
            "duration_seconds": duration,
            "progress_percentage": (position_seconds / duration * 100) if duration > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting position: {str(e)}"
        )


@router.get("/volume")
async def get_volume(
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Get current volume level.
    
    Returns the current volume level (0-100).
    """
    try:
        volume = audio_service.get_volume()
        
        return {
            "volume": volume,
            "is_muted": volume == 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting volume: {str(e)}"
        )


# ADVANCED ENDPOINTS

@router.post("/skip-forward")
async def skip_forward(
    skip_data: SkipRequest = SkipRequest(),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Skip forward by specified seconds.
    
    Jumps forward in the current song by the specified number of seconds.
    """
    try:
        if not audio_service.is_song_loaded():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No song loaded for skipping"
            )
        
        success = audio_service.skip_forward(skip_data.seconds)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to skip forward"
            )
        
        new_position = audio_service.get_position()
        
        return {
            "message": f"Skipped forward {skip_data.seconds} seconds",
            "seconds_skipped": skip_data.seconds,
            "new_position": new_position
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error skipping forward: {str(e)}"
        )


@router.post("/skip-backward")
async def skip_backward(
    skip_data: SkipRequest = SkipRequest(),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Skip backward by specified seconds.
    
    Jumps backward in the current song by the specified number of seconds.
    """
    try:
        if not audio_service.is_song_loaded():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No song loaded for skipping"
            )
        
        success = audio_service.skip_backward(skip_data.seconds)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to skip backward"
            )
        
        new_position = audio_service.get_position()
        
        return {
            "message": f"Skipped backward {skip_data.seconds} seconds",
            "seconds_skipped": skip_data.seconds,
            "new_position": new_position
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error skipping backward: {str(e)}"
        )


@router.put("/playlist/{playlist_id}")
async def set_current_playlist(
    playlist_id: str = Depends(validate_playlist_id),
    position: int = Query(0, ge=0, description="Starting position in playlist"),
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    audio_service: AudioService = Depends(get_audio_service)
):
    """Set the current active playlist and start playing."""
    try:
        print(f"[PLAYER] ===== CHANGING PLAYLIST =====")
        print(f"[PLAYER] Requested playlist: {playlist_id}")
        print(f"[PLAYER] Position: {position}")
        
        playlist = playlist_service.get_playlist_by_id(playlist_id)
        if not playlist:
            raise PlaylistNotFoundError(playlist_id)
        
        print(f"[PLAYER] Found playlist: {playlist.name}")
        print(f"[PLAYER] Playlist has {playlist.song_count} songs")
        
        # Permitir playlists vacías
        if playlist.is_empty():
            print(f"[PLAYER] Setting empty playlist: {playlist.name}")
            player_manager.set_current_playlist(playlist)
            
            return {
                "message": "Current playlist updated (empty)",
                "success": True,
                "playlist_id": playlist_id,
                "playlist_name": playlist.name,
                "song_count": 0,
                "current_position": 0,
                "current_song": None,
                "is_playing": False
            }
        
        # Validar posición
        if position >= playlist.song_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid position. Playlist has {playlist.song_count} songs"
            )
        
        print(f"[PLAYER] Stopping current audio...")
        audio_service.stop()
        
        print(f"[PLAYER] Setting playlist in manager...")
        player_manager.set_current_playlist(playlist)
        
        print(f"[PLAYER] Setting position to {position}...")
        playlist.set_current_position(position)
        
        current_song = playlist.get_current_song()
        print(f"[PLAYER] Current song: {current_song.title if current_song else 'None'}")
        
        if current_song:
            print(f"[PLAYER] Loading song: {current_song.title}")
            
            if audio_service.load_song(current_song):
                print(f"[PLAYER] Song loaded successfully")
                if audio_service.play():
                    print(f"[PLAYER] Playing: {current_song.title}")
                else:
                    print(f"[PLAYER] WARNING: Failed to start playback")
            else:
                print(f"[PLAYER] ERROR: Failed to load song")
        
        print(f"[PLAYER] ===== PLAYLIST CHANGE COMPLETE =====")
        
        return {
            "message": "Current playlist updated and playing",
            "success": True,
            "playlist_id": playlist_id,
            "playlist_name": playlist.name,
            "song_count": playlist.song_count,
            "current_position": position,
            "current_song": current_song.get_display_name() if current_song else None,
            "is_playing": audio_service.is_playing()
        }
        
    except (PlaylistNotFoundError, HTTPException):
        raise
    except Exception as e:
        print(f"[PLAYER] CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting current playlist: {str(e)}"
        )
    
    
# UTILITY ENDPOINTS

@router.get("/controls", response_model=PlayerControls)
async def get_available_controls(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Get information about available player controls.
    
    Returns which controls are currently available based on player state.
    """
    try:
        has_playlist = player_manager.current_playlist and not player_manager.current_playlist.is_empty()
        has_song_loaded = audio_service.is_song_loaded()
        is_playing = audio_service.is_playing()
        
        return PlayerControls(
            can_play=has_playlist and not is_playing,
            can_pause=is_playing,
            can_stop=is_playing or audio_service.is_paused(),
            can_next=has_playlist and player_manager.current_playlist.has_next(),
            can_previous=has_playlist and player_manager.current_playlist.has_previous(),
            can_seek=has_song_loaded
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available controls: {str(e)}"
        )


@router.post("/toggle-repeat")
async def toggle_repeat_mode(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager)
):
    """
    Toggle between repeat modes.
    
    Cycles through: off -> one -> all -> off
    """
    try:
        new_mode = player_manager.toggle_repeat_mode()
        
        return {
            "message": "Repeat mode toggled",
            "repeat_mode": new_mode
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling repeat mode: {str(e)}"
        )


@router.post("/toggle-shuffle")
async def toggle_shuffle_mode(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager)
):
    """
    Toggle shuffle mode on/off.
    
    Enables or disables shuffle mode for the current playlist.
    """
    try:
        new_mode = player_manager.toggle_shuffle_mode()
        
        return {
            "message": f"Shuffle mode {'enabled' if new_mode else 'disabled'}",
            "shuffle_mode": new_mode
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling shuffle mode: {str(e)}"
        )


@router.post("/mute")
async def toggle_mute(
    player_manager: MusicPlayerManager = Depends(get_music_player_manager),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Toggle mute on/off.
    
    Mutes or unmutes audio while preserving volume level.
    """
    try:
        if player_manager.is_muted():
            player_manager.unmute()
            audio_service.set_volume(player_manager.current_volume)
            message = "Audio unmuted"
        else:
            player_manager.mute()
            audio_service.set_volume(0)
            message = "Audio muted"
        
        return {
            "message": message,
            "is_muted": player_manager.is_muted(),
            "volume": player_manager.current_volume
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling mute: {str(e)}"
        )


         