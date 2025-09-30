from typing import Optional
from models.playlist import Playlist


class MusicPlayerManager:
    
    # Class attribute to store the single instance
    _instance: Optional['MusicPlayerManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'MusicPlayerManager':
        if cls._instance is None:
            cls._instance = super(MusicPlayerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        # Prevent multiple initializations of the same instance
        if MusicPlayerManager._initialized:
            return
        
        # Player state attributes
        self.current_playlist: Optional[Playlist] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.current_volume: float = 70.0  # Default volume 70%
        self.repeat_mode: str = "off"  # "off", "one", "all"
        self.shuffle_mode: bool = False
        self.current_position_seconds: float = 0.0
        
        # Valid repeat modes
        self._valid_repeat_modes = {"off", "one", "all"}
        
        # Mark as initialized
        MusicPlayerManager._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'MusicPlayerManager':

        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_current_playlist(self, playlist: Playlist) -> None:

        if not isinstance(playlist, Playlist):
            raise ValueError("Invalid playlist object")
        
        self.current_playlist = playlist
        self.current_position_seconds = 0.0  # Reset position when changing playlist
        
        # Reset playback state when changing playlist
        self.is_playing = False
        self.is_paused = False
    
    def get_current_playlist(self) -> Optional[Playlist]:
   
        return self.current_playlist
    
    def set_playing_state(self, is_playing: bool) -> None:
 
        self.is_playing = bool(is_playing)
        
        # Update paused state accordingly
        if self.is_playing:
            self.is_paused = False
        else:
            # If not playing, it could be paused (if there was music) or stopped
            if self.current_playlist and not self.current_playlist.is_empty():
                self.is_paused = True
    
    def set_volume(self, volume: float) -> None:
        
        if not 0.0 <= volume <= 100.0:
            raise ValueError("Volume must be between 0.0 and 100.0")
        
        self.current_volume = float(volume)
    
    def toggle_repeat_mode(self) -> str:
        
        if self.repeat_mode == "off":
            self.repeat_mode = "one"
        elif self.repeat_mode == "one":
            self.repeat_mode = "all"
        else:  # "all"
            self.repeat_mode = "off"
        
        return self.repeat_mode
    
    def set_repeat_mode(self, mode: str) -> None:
        
        if mode not in self._valid_repeat_modes:
            raise ValueError(f"Invalid repeat mode '{mode}'. Must be one of: {', '.join(self._valid_repeat_modes)}")
        
        self.repeat_mode = mode
    
    def toggle_shuffle_mode(self) -> bool:
        
        self.shuffle_mode = not self.shuffle_mode
        
        # If shuffle is turned on and we have a playlist, shuffle it
        if self.shuffle_mode and self.current_playlist and not self.current_playlist.is_empty():
            self.current_playlist.shuffle_songs()
        
        return self.shuffle_mode
    
    def set_shuffle_mode(self, shuffle: bool) -> None:
        
        self.shuffle_mode = bool(shuffle)
        
        # If shuffle is turned on and we have a playlist, shuffle it
        if self.shuffle_mode and self.current_playlist and not self.current_playlist.is_empty():
            self.current_playlist.shuffle_songs()
    
    def update_position(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("Position cannot be negative")
        
        self.current_position_seconds = float(seconds)
    
    def reset_state(self) -> None:
        
        self.current_playlist = None
        self.is_playing = False
        self.is_paused = False
        self.current_volume = 70.0
        self.repeat_mode = "off"
        self.shuffle_mode = False
        self.current_position_seconds = 0.0
    
    def get_state_summary(self) -> dict:
        
        current_song = None
        playlist_info = None
        
        if self.current_playlist:
            current_song = self.current_playlist.get_current_song()
            playlist_info = {
                "name": self.current_playlist.name,
                "song_count": self.current_playlist.song_count,
                "current_position": self.current_playlist.current_position
            }
        
        return {
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "volume": self.current_volume,
            "repeat_mode": self.repeat_mode,
            "shuffle_mode": self.shuffle_mode,
            "position_seconds": self.current_position_seconds,
            "current_song": current_song.get_display_name() if current_song else None,
            "playlist": playlist_info
        }
    
    def is_muted(self) -> bool:
        
        return self.current_volume == 0.0
    
    def mute(self) -> None:
        """Mute the player by setting volume to 0."""
        self._volume_before_mute = self.current_volume
        self.current_volume = 0.0
    
    def unmute(self) -> None:
        """Unmute the player by restoring previous volume."""
        if hasattr(self, '_volume_before_mute'):
            self.current_volume = self._volume_before_mute
        else:
            self.current_volume = 70.0  # Default volume
    
    def has_current_song(self) -> bool:
        
        return (self.current_playlist is not None and 
                not self.current_playlist.is_empty() and
                self.current_playlist.get_current_song() is not None)
    
    def next_song(self) -> bool:
        
        if not self.current_playlist:
            return False
        
        # Handle repeat one mode
        if self.repeat_mode == "one":
            # Stay on the same song, just reset position
            self.current_position_seconds = 0.0
            return True
        
        # Try to move to next song
        next_song = self.current_playlist.next_song()
        
        if next_song:
            self.current_position_seconds = 0.0
            return True
        
        # If at the end and repeat all is enabled, go to first song
        if self.repeat_mode == "all" and self.current_playlist.song_count > 0:
            self.current_playlist.set_current_position(0)
            self.current_position_seconds = 0.0
            return True
        
        # If we reach here, we're at the end and repeat is off
        self.is_playing = False
        self.is_paused = False
        return False
    
    def previous_song(self) -> bool:
        
        if not self.current_playlist:
            return False
        
        # Handle repeat one mode
        if self.repeat_mode == "one":
            # Stay on the same song, just reset position
            self.current_position_seconds = 0.0
            return True
        
        # Try to move to previous song
        prev_song = self.current_playlist.previous_song()
        
        if prev_song:
            self.current_position_seconds = 0.0
            return True
        
        # If at the beginning and repeat all is enabled, go to last song
        if self.repeat_mode == "all" and self.current_playlist.song_count > 0:
            last_position = self.current_playlist.song_count - 1
            self.current_playlist.set_current_position(last_position)
            self.current_position_seconds = 0.0
            return True
        
        return False
    
    def __str__(self) -> str:
        """String representation of the music player manager."""
        status = "Playing" if self.is_playing else ("Paused" if self.is_paused else "Stopped")
        playlist_name = self.current_playlist.name if self.current_playlist else "None"
        return f"MusicPlayer(Status: {status}, Playlist: {playlist_name}, Volume: {self.current_volume}%)"
    
    def __repr__(self) -> str:
        """Detailed representation of the music player manager."""
        return f"MusicPlayerManager(instance_id={id(self)}, playlist={self.current_playlist}, playing={self.is_playing})"


# Example usage and testing
if __name__ == "__main__":
    print("Testing Singleton Pattern Implementation")
    
    # Test singleton behavior
    player1 = MusicPlayerManager()
    player2 = MusicPlayerManager()
    player3 = MusicPlayerManager.get_instance()
    
    print(f"player1 id: {id(player1)}")
    print(f"player2 id: {id(player2)}")
    print(f"player3 id: {id(player3)}")
    print(f"All instances are the same: {player1 is player2 is player3}")
    
    # Test player functionality
    player1.set_volume(80.0)
    print(f"Volume set on player1: {player1.current_volume}")
    print(f"Volume on player2: {player2.current_volume}")
    
    player2.toggle_repeat_mode()
    print(f"Repeat mode toggled on player2: {player2.repeat_mode}")
    print(f"Repeat mode on player1: {player1.repeat_mode}")
    
    print(f"\nPlayer state: {player1}")
    print("Singleton pattern working correctly!")