import pygame
import threading
import time
import vlc
from typing import Optional, Callable
from models.song import Song
from patterns.singleton import MusicPlayerManager


class AudioService:
    """
    Service for handling audio playback operations.
    
    This class provides a comprehensive interface for audio playback,
    integrating with pygame.mixer and the MusicPlayerManager singleton.
    """
    
    def __init__(self):
        """Initialize the audio service with pygame mixer."""
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self.player_manager = MusicPlayerManager.get_instance()
            
            self.current_song: Optional[Song] = None
            self.is_loaded: bool = False
            self.start_time: float = 0.0
            self.pause_time: float = 0.0
            
            # VLC player para seek
            self.vlc_instance = vlc.Instance()
            self.vlc_player = self.vlc_instance.media_player_new()
            
            # Callbacks
            self.on_song_finished: Optional[Callable] = None
            self.on_playback_error: Optional[Callable[[str], None]] = None
            
            # Position tracking thread
            self._position_thread: Optional[threading.Thread] = None
            self._stop_position_tracking: bool = False
            
            # Control de múltiples cargas
            self._loading_lock = threading.Lock()
            self._is_loading = False
            
            # Supported formats
            self.supported_formats = {'.mp3', '.wav', '.flac'}
            
        except pygame.error as e:
            raise RuntimeError(f"Failed to initialize audio system: {e}")
    
    def _force_stop_all_audio(self):
        """CRÍTICO: Forzar detención completa de todo audio"""
        try:
            # Detener mixer completamente
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            # Detener thread de seguimiento
            self._stop_position_tracking_thread()
            
            # Resetear estados
            self.is_loaded = False
            self.start_time = 0.0
            self.pause_time = 0.0
            
            # Actualizar manager
            self.player_manager.set_playing_state(False)
            self.player_manager.update_position(0.0)
            
            print("[AUDIO] Force stopped all audio")
            
        except Exception as e:
            print(f"[AUDIO] Error in force stop: {e}")
    
    def load_song(self, song: Song) -> bool:
        """CRÍTICO: Cargar canción con control de múltiples llamadas"""
        with self._loading_lock:
            if self._is_loading:
                print("[AUDIO] Already loading, skipping duplicate load")
                return False
            
            self._is_loading = True
            
        try:
            print(f"[AUDIO] Loading song: {song.title}")
            
            # PASO 1: Detener completamente audio anterior
            self._force_stop_all_audio()
            
            # PASO 2: Validar archivo
            if not song.is_valid_file():
                if self.on_playback_error:
                    self.on_playback_error(f"File not found: {song.file_path}")
                return False
            
            if song.get_file_extension() not in self.supported_formats:
                if self.on_playback_error:
                    self.on_playback_error(f"Unsupported format: {song.format}")
                return False
            
            # PASO 3: Cargar nueva canción
            pygame.mixer.music.load(song.file_path)
            self.current_song = song
            self.is_loaded = True
            
            print(f"[AUDIO] Successfully loaded: {song.title}")
            return True
            
        except pygame.error as e:
            print(f"[AUDIO] Error loading song: {e}")
            if self.on_playback_error:
                self.on_playback_error(f"Failed to load song: {e}")
            return False
        finally:
            self._is_loading = False
    
    def play(self) -> bool:
        """Start or resume playback."""
        try:
            if not self.is_loaded or not self.current_song:
                print("[AUDIO] No song loaded for playback")
                return False
            
            if self.is_paused():
                pygame.mixer.music.unpause()
                self.start_time += time.time() - self.pause_time
                print("[AUDIO] Resumed from pause")
            else:
                pygame.mixer.music.play()
                self.start_time = time.time()
                print(f"[AUDIO] Started playing: {self.current_song.title}")
            
            self.player_manager.set_playing_state(True)
            
            # CRÍTICO: Iniciar position tracking
            self._start_position_tracking()
            print("[AUDIO] Position tracking started")
            
            return True
            
        except pygame.error as e:
            print(f"[AUDIO] Play error: {e}")
            if self.on_playback_error:
                self.on_playback_error(f"Playback error: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause playback"""
        try:
            if self.is_playing():
                pygame.mixer.music.pause()
                self.pause_time = time.time()
                self.player_manager.set_playing_state(False)
                self._stop_position_tracking_thread()
                print("[AUDIO] Paused")
                return True
            return False
            
        except pygame.error as e:
            if self.on_playback_error:
                self.on_playback_error(f"Pause error: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop playback and reset position"""
        try:
            self._force_stop_all_audio()
            print("[AUDIO] Stopped")
            return True
            
        except pygame.error as e:
            if self.on_playback_error:
                self.on_playback_error(f"Stop error: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """Set playback volume"""
        try:
            if not 0.0 <= volume <= 100.0:
                return False
            
            pygame_volume = volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
            self.player_manager.set_volume(volume)
            
            return True
            
        except pygame.error as e:
            if self.on_playback_error:
                self.on_playback_error(f"Volume error: {e}")
            return False
    
    def get_volume(self) -> float:
        """Get current volume level"""
        return self.player_manager.current_volume
    
    def seek(self, position_seconds: float) -> bool:
        """Seek usando VLC player para mayor precisión."""
        try:
            print(f"[AUDIO] Seek request to {position_seconds:.1f}s using VLC")
            
            if not self.current_song or position_seconds < 0:
                print(f"[AUDIO] Seek failed: no song or invalid position")
                return False
            
            if position_seconds > self.current_song.duration:
                position_seconds = self.current_song.duration
                print(f"[AUDIO] Position clamped to {position_seconds:.1f}s")
            
            was_playing = self.is_playing()
            
            # CRÍTICO: Detener el tracking antes de hacer cambios
            self._stop_position_tracking_thread()
            
            # Detener pygame
            pygame.mixer.music.stop()
            
            # Cargar canción en VLC si no está cargada
            media = self.vlc_instance.media_new(self.current_song.file_path)
            self.vlc_player.set_media(media)
            
            # Hacer seek en VLC
            duration_ms = int(self.current_song.duration * 1000)
            position_ms = int(position_seconds * 1000)
            
            # Iniciar reproducción en VLC
            self.vlc_player.play()
            
            # Esperar que VLC esté listo
            time.sleep(0.1)
            
            # Hacer el seek
            self.vlc_player.set_time(position_ms)
            
            print(f"[AUDIO] VLC seek to {position_seconds:.1f}s completed")
            
            # Ajustar volumen de VLC
            vlc_volume = int(self.player_manager.current_volume)
            self.vlc_player.audio_set_volume(vlc_volume)
            
            # Detener VLC y volver a pygame después del seek
            time.sleep(0.2)
            self.vlc_player.stop()
            
            # Reiniciar pygame en la nueva posición
            pygame.mixer.music.load(self.current_song.file_path)
            pygame.mixer.music.play(start=position_seconds)
            
            # Actualizar tiempos para tracking
            current_time = time.time()
            self.start_time = current_time - position_seconds
            
            if was_playing:
                self.player_manager.set_playing_state(True)
                # CRÍTICO: Reiniciar el tracking
                self._start_position_tracking()
                print("[AUDIO] Position tracking restarted after seek")
            else:
                pygame.mixer.music.pause()
                self.pause_time = current_time
            
            # Actualizar posición en manager
            self.player_manager.update_position(position_seconds)
            
            print(f"[AUDIO] Seek completed successfully to {position_seconds:.1f}s")
            return True
            
        except Exception as e:
            print(f"[AUDIO] Error during VLC seek: {e}")
            import traceback
            traceback.print_exc()
            if self.on_playback_error:
                self.on_playback_error(f"Seek error: {e}")
            return False
        

    # También necesitamos mejorar get_position para ser más preciso:
    def get_position(self) -> float:
        """Get current playback position - VERSIÓN MEJORADA"""
        if not self.is_loaded or not self.current_song:
            return 0.0
        
        current_time = time.time()
        
        if self.is_playing():
            # Calcular posición basada en tiempo transcurrido desde start_time
            position = current_time - self.start_time
            # Asegurar que no exceda la duración
            return min(max(0.0, position), self.current_song.duration)
        elif self.is_paused():
            # Si está pausado, usar el tiempo cuando se pausó
            position = self.pause_time - self.start_time
            return min(max(0.0, position), self.current_song.duration)
        
        return 0.0
    
    def get_position(self) -> float:
        """Get current playback position in seconds"""
        if not self.is_loaded or not self.current_song:
            return 0.0
        
        if self.is_playing():
            current_time = time.time()
            position = current_time - self.start_time
            return min(max(0.0, position), self.current_song.duration)
        elif self.is_paused():
            position = self.pause_time - self.start_time
            return min(max(0.0, position), self.current_song.duration)
        
        return 0.0
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return pygame.mixer.music.get_busy() and not self.is_paused()
    
    def is_paused(self) -> bool:
        """Check if audio is currently paused"""
        return self.player_manager.is_paused
    
    def skip_forward(self, seconds: int = 10) -> bool:
        """Skip forward by specified seconds"""
        current_pos = self.get_position()
        new_position = current_pos + seconds
        return self.seek(new_position)
    
    def skip_backward(self, seconds: int = 10) -> bool:
        """Skip backward by specified seconds"""
        current_pos = self.get_position()
        new_position = max(0.0, current_pos - seconds)
        return self.seek(new_position)
    
    def _start_position_tracking(self) -> None:
        """Start position tracking thread."""
        # CRÍTICO: Detener thread anterior si existe
        if self._position_thread and self._position_thread.is_alive():
            print("[AUDIO] Stopping existing position tracker")
            self._stop_position_tracking_thread()
        
        print("[AUDIO] Starting new position tracking thread")
        self._stop_position_tracking = False
        self._position_thread = threading.Thread(target=self._position_tracker, daemon=True)
        self._position_thread.start()
    
    def _stop_position_tracking_thread(self) -> None:
        """Stop position tracking thread."""
        print("[AUDIO] Requesting position tracker to stop")
        self._stop_position_tracking = True
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=1.0)
            print("[AUDIO] Position tracker stopped")
    
    def _position_tracker(self) -> None:
        """Track playback position and handle song end."""
        print("[AUDIO] Position tracker thread started")
        
        while not self._stop_position_tracking:
            try:
                if self.is_playing() and self.current_song:
                    current_pos = self.get_position()
                    self.player_manager.update_position(current_pos)
                    
                    # Debug: mostrar posición cada 5 segundos
                    if int(current_pos) % 5 == 0:
                        print(f"[AUDIO] Position: {current_pos:.1f}s / {self.current_song.duration:.1f}s")
                    
                    # Verificar si la canción terminó
                    if current_pos >= self.current_song.duration - 0.5:
                        print(f"[AUDIO] !!! SONG REACHED END !!! ({current_pos:.1f}s >= {self.current_song.duration - 0.5:.1f}s)")
                        self._handle_song_finished()
                        break
                    
                    # CRÍTICO: También verificar si pygame terminó
                    if not pygame.mixer.music.get_busy():
                        print("[AUDIO] !!! PYGAME STOPPED !!! Song finished")
                        self._handle_song_finished()
                        break
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[AUDIO] ERROR in position tracker: {e}")
                import traceback
                traceback.print_exc()
                if self.on_playback_error:
                    self.on_playback_error(f"Position tracking error: {e}")
                break
    
    print("[AUDIO] Position tracker thread ended")

    def _handle_song_finished(self) -> None:
        """Handle when a song finishes playing."""
        print("[AUDIO] ========================================")
        print("[AUDIO] SONG FINISHED - HANDLING AUTO-NEXT")
        print("[AUDIO] ========================================")
    
        try:
            # Detener audio actual
            self.stop()
            print("[AUDIO] Current song stopped")
            
            # Obtener estado del player
            repeat_mode = self.player_manager.repeat_mode
            shuffle_mode = self.player_manager.shuffle_mode
            
            print(f"[AUDIO] Repeat mode: {repeat_mode}")
            print(f"[AUDIO] Shuffle mode: {shuffle_mode}")
            
            if not self.player_manager.current_playlist:
                print("[AUDIO] No current playlist - stopping")
                return
            
            current_playlist = self.player_manager.current_playlist
            print(f"[AUDIO] Current playlist: {current_playlist.name}")
            print(f"[AUDIO] Current position: {current_playlist.current_position}")
            print(f"[AUDIO] Total songs: {current_playlist.song_count}")
            
            # Lógica según modo de repetición
            if repeat_mode == "one":
                # Repetir la misma canción
                print("[AUDIO] REPEAT ONE - Replaying same song")
                current_song = current_playlist.get_current_song()
                if current_song:
                    print(f"[AUDIO] Reloading: {current_song.title}")
                    if self.load_song(current_song):
                        self.play()
                        print("[AUDIO] Song replayed successfully")
                    else:
                        print("[AUDIO] ERROR: Failed to reload song")
            
            elif repeat_mode == "all" or repeat_mode == "off":
                # Intentar siguiente canción
                print("[AUDIO] Attempting to go to next song...")
                
                next_success = self.player_manager.next_song()
                print(f"[AUDIO] Next song success: {next_success}")
                
                if next_success:
                    next_song = current_playlist.get_current_song()
                    if next_song:
                        print(f"[AUDIO] Loading next song: {next_song.title}")
                        if self.load_song(next_song):
                            self.play()
                            print("[AUDIO] Next song playing successfully")
                        else:
                            print("[AUDIO] ERROR: Failed to load next song")
                    else:
                        print("[AUDIO] ERROR: No next song found")
                else:
                    # No hay más canciones
                    print("[AUDIO] No more songs available")
                    
                    if repeat_mode == "all":
                        # Volver al inicio de la playlist
                        print("[AUDIO] REPEAT ALL - Going back to start")
                        current_playlist.set_current_position(0)
                        first_song = current_playlist.get_current_song()
                        
                        if first_song:
                            print(f"[AUDIO] Loading first song: {first_song.title}")
                            if self.load_song(first_song):
                                self.play()
                                print("[AUDIO] Playlist restarted successfully")
                            else:
                                print("[AUDIO] ERROR: Failed to load first song")
                        else:
                            print("[AUDIO] ERROR: No first song found")
                    else:
                        print("[AUDIO] Playlist ended - stopping playback")
            
            print("[AUDIO] ========================================")
            print("[AUDIO] SONG FINISHED HANDLER COMPLETED")
            print("[AUDIO] ========================================")
            
        except Exception as e:
            print(f"[AUDIO] CRITICAL ERROR in _handle_song_finished: {e}")
            import traceback
            traceback.print_exc()
            
            
    def set_song_finished_callback(self, callback: Callable) -> None:
        """Set callback for when song finishes"""
        self.on_song_finished = callback
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for playback errors"""
        self.on_playback_error = callback
    
    def get_current_song(self) -> Optional[Song]:
        """Get currently loaded song"""
        return self.current_song
    
    def is_song_loaded(self) -> bool:
        """Check if a song is loaded"""
        return self.is_loaded and self.current_song is not None
    
    def cleanup(self) -> None:
        """Clean up audio resources including VLC."""
        try:
            print("[AUDIO] Cleaning up audio service")
            self._stop_position_tracking_thread()
            self._force_stop_all_audio()
            
            # Limpiar VLC
            if hasattr(self, 'vlc_player'):
                self.vlc_player.stop()
                self.vlc_player.release()
            
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup"""
        self.cleanup()