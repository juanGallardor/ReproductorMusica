import pygame
import threading
import time
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
            
            # Callbacks
            self.on_song_finished: Optional[Callable] = None
            self.on_playback_error: Optional[Callable[[str], None]] = None
            
            # Position tracking thread
            self._position_thread: Optional[threading.Thread] = None
            self._stop_position_tracking: bool = False
            
            # CRÍTICO: Control de múltiples cargas
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
        """Start or resume playback - CON CONTROL MEJORADO"""
        try:
            if not self.is_loaded or not self.current_song:
                print("[AUDIO] No song loaded for playback")
                return False
            
            if self.is_paused():
                # Reanudar desde pausa
                pygame.mixer.music.unpause()
                self.start_time += time.time() - self.pause_time
                print("[AUDIO] Resumed from pause")
            else:
                # Iniciar desde el principio
                pygame.mixer.music.play()
                self.start_time = time.time()
                print(f"[AUDIO] Started playing: {self.current_song.title}")
            
            self.player_manager.set_playing_state(True)
            self._start_position_tracking()
            
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
        """
        Seek simulado para pygame.mixer - VERSIÓN MEJORADA
        
        Como pygame.mixer no soporta seek real, simulamos la posición
        manteniendo la consistencia visual en el frontend.
        """
        try:
            print(f"[AUDIO] Seek request to {position_seconds:.1f}s")
            
            if not self.current_song or position_seconds < 0:
                print(f"[AUDIO] Seek failed: no song or invalid position")
                return False
            
            if position_seconds > self.current_song.duration:
                position_seconds = self.current_song.duration
                print(f"[AUDIO] Position clamped to {position_seconds:.1f}s")
            
            was_playing = self.is_playing()
            
            # ESTRATEGIA: En lugar de intentar seek real, 
            # ajustamos los tiempos para simular la posición
            
            current_time = time.time()
            
            if was_playing:
                # Si está reproduciendo, reiniciamos pero ajustamos start_time
                pygame.mixer.music.stop()
                pygame.mixer.music.play()
                # Ajustar start_time para que get_position() devuelva position_seconds
                self.start_time = current_time - position_seconds
                self.player_manager.set_playing_state(True)
                print(f"[AUDIO] Simulated seek while playing to {position_seconds:.1f}s")
            else:
                # Si está pausado, solo ajustamos los tiempos sin reproducir
                self.start_time = current_time - position_seconds
                self.pause_time = current_time
                print(f"[AUDIO] Simulated seek while paused to {position_seconds:.1f}s")
            
            # Actualizar posición en el manager
            self.player_manager.update_position(position_seconds)
            
            # Reiniciar tracking si está reproduciendo
            if was_playing:
                self._start_position_tracking()
            
            print(f"[AUDIO] Seek simulation completed to {position_seconds:.1f}s")
            return True
            
        except Exception as e:
            print(f"[AUDIO] Error during seek simulation: {e}")
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
        """Start position tracking thread"""
        if self._position_thread and self._position_thread.is_alive():
            return
        
        self._stop_position_tracking = False
        self._position_thread = threading.Thread(target=self._position_tracker, daemon=True)
        self._position_thread.start()
    
    def _stop_position_tracking_thread(self) -> None:
        """Stop position tracking thread"""
        self._stop_position_tracking = True
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=1.0)
    
    def _position_tracker(self) -> None:
        """Track playback position and handle song end"""
        while not self._stop_position_tracking:
            try:
                if self.is_playing() and self.current_song:
                    current_pos = self.get_position()
                    self.player_manager.update_position(current_pos)
                    
                    # Check if song finished
                    if current_pos >= self.current_song.duration - 0.5:
                        print("[AUDIO] Song finished, triggering next")
                        self._handle_song_finished()
                        break
                
                time.sleep(0.1)  # Update every 100ms
                
            except Exception as e:
                if self.on_playback_error:
                    self.on_playback_error(f"Position tracking error: {e}")
                break
    
    def _handle_song_finished(self) -> None:
        """Handle when a song finishes playing"""
        print("[AUDIO] Handling song finished")
        self.stop()
        
        if self.on_song_finished:
            self.on_song_finished()
        else:
            # Default behavior: try to play next song
            if self.player_manager.next_song():
                next_song = self.player_manager.get_current_playlist().get_current_song()
                if next_song:
                    print(f"[AUDIO] Auto-playing next: {next_song.title}")
                    if self.load_song(next_song):
                        self.play()
    
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
        """Clean up audio resources"""
        try:
            print("[AUDIO] Cleaning up audio service")
            self._stop_position_tracking_thread()
            self._force_stop_all_audio()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def __del__(self) -> None:
        """Destructor to ensure cleanup"""
        self.cleanup()