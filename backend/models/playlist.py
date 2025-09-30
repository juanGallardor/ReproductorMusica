import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .doubly_linked_list import DoublyLinkedList
from .song import Song


class Playlist:
    """
    Playlist model that manages songs using a doubly linked list.
    
    This class provides a high-level interface for playlist operations
    while leveraging the efficient navigation capabilities of the
    doubly linked list data structure.
    """
    
    def __init__(self, name: str, description: Optional[str] = None, 
                 cover_image: Optional[str] = None, playlist_id: Optional[str] = None):
        """
        Initialize a new playlist.
        
        Args:
            name: Name of the playlist
            description: Optional description
            cover_image: Optional path to cover image
            playlist_id: Optional ID (generates new if not provided)
            
        Raises:
            ValueError: If name is empty or invalid
        """
        if not name or not name.strip():
            raise ValueError("Playlist name cannot be empty")
        
        self.id: str = playlist_id or str(uuid.uuid4())
        self.name: str = name.strip()
        self.description: Optional[str] = description.strip() if description else None
        self.cover_image: Optional[str] = cover_image
        self.songs: DoublyLinkedList = DoublyLinkedList()
        self.current_position: int = 0
        self.created_at: datetime = datetime.now()
        self.total_duration: float = 0.0
        self.song_count: int = 0
    
    def add_song(self, song: Song, position: Optional[int] = None) -> bool:
        """
        Add a song to the playlist.
        
        Args:
            song: Song object to add
            position: Optional position to insert at (None = end of list)
            
        Returns:
            bool: True if song was added successfully, False otherwise
            
        Raises:
            ValueError: If song is None or position is invalid
        """
        if not isinstance(song, Song):
            raise ValueError("Invalid song object")
        
        try:
            if position is None:
                # Add to end of playlist
                self.songs.insert_at_end(song)
            else:
                # Add at specific position
                if position < 0 or position > self.songs.size():
                    raise ValueError(f"Invalid position {position}. Must be between 0 and {self.songs.size()}")
                self.songs.insert_at_position(song, position)
            
            self.update_totals()
            
            # Set as current if this is the first song
            if self.songs.size() == 1:
                self.current_position = 0
                self.songs.set_current(0)
            
            return True
            
        except Exception as e:
            print(f"Error adding song: {e}")
            return False
    
    def remove_song(self, song_id: str) -> bool:
        """
        Remove a song from the playlist by ID.
        
        Args:
            song_id: ID of the song to remove
            
        Returns:
            bool: True if song was removed, False if not found
        """
        if not song_id:
            return False
        
        try:
            # Find the song in the list
            current = self.songs.head
            position = 0
            
            while current:
                if current.data.id == song_id:
                    # Adjust current position if needed
                    if position < self.current_position:
                        self.current_position -= 1
                    elif position == self.current_position and self.current_position >= self.songs.size() - 1:
                        self.current_position = max(0, self.songs.size() - 2)
                    
                    # Remove the song
                    self.songs.delete_at_position(position)
                    self.update_totals()
                    
                    # Update current position in songs list
                    if not self.songs.is_empty() and self.current_position < self.songs.size():
                        self.songs.set_current(self.current_position)
                    else:
                        self.current_position = 0
                    
                    return True
                
                current = current.next
                position += 1
            
            return False
            
        except Exception as e:
            print(f"Error removing song: {e}")
            return False
    
    def remove_song_at_position(self, position: int) -> bool:
        """
        Remove a song at the specified position.
        
        Args:
            position: Position of the song to remove (0-indexed)
            
        Returns:
            bool: True if song was removed, False otherwise
            
        Raises:
            ValueError: If position is invalid
        """
        if self.songs.is_empty():
            return False
        
        if position < 0 or position >= self.songs.size():
            raise ValueError(f"Invalid position {position}. Must be between 0 and {self.songs.size() - 1}")
        
        try:
            # Adjust current position if needed
            if position < self.current_position:
                self.current_position -= 1
            elif position == self.current_position and self.current_position >= self.songs.size() - 1:
                self.current_position = max(0, self.songs.size() - 2)
            
            self.songs.delete_at_position(position)
            self.update_totals()
            
            # Update current position in songs list
            if not self.songs.is_empty() and self.current_position < self.songs.size():
                self.songs.set_current(self.current_position)
            else:
                self.current_position = 0
            
            return True
            
        except Exception as e:
            print(f"Error removing song at position: {e}")
            return False
    
    def find_song(self, song_id: str) -> Optional[Song]:
        """
        Find a song by ID.
        
        Args:
            song_id: ID of the song to find
            
        Returns:
            Optional[Song]: The song if found, None otherwise
        """
        if not song_id or self.songs.is_empty():
            return None
        
        current = self.songs.head
        while current:
            if current.data.id == song_id:
                return current.data
            current = current.next
        
        return None
    
    def get_song_at_position(self, position: int) -> Optional[Song]:
        """
        Get the song at the specified position.
        
        Args:
            position: Position of the song (0-indexed)
            
        Returns:
            Optional[Song]: The song at the position, None if invalid position
        """
        try:
            if position < 0 or position >= self.songs.size():
                return None
            return self.songs.get_at_position(position)
        except Exception:
            return None
    
    def clear_all_songs(self) -> None:
        """Remove all songs from the playlist."""
        self.songs.clear()
        self.current_position = 0
        self.update_totals()
    
    def get_current_song(self) -> Optional[Song]:
        """
        Get the currently selected song.
        
        Returns:
            Optional[Song]: Current song or None if playlist is empty
        """
        if self.songs.is_empty():
            return None
        
        try:
            return self.songs.get_current()
        except Exception:
            return None
    
    def next_song(self) -> Optional[Song]:
        """
        Move to the next song in the playlist.
        
        Returns:
            Optional[Song]: Next song or None if at end
        """
        if self.songs.is_empty():
            return None
        
        next_song = self.songs.next()
        if next_song:
            self.current_position += 1
        
        return next_song
    
    def previous_song(self) -> Optional[Song]:
        """
        Move to the previous song in the playlist.
        
        Returns:
            Optional[Song]: Previous song or None if at beginning
        """
        if self.songs.is_empty():
            return None
        
        prev_song = self.songs.previous()
        if prev_song:
            self.current_position -= 1
        
        return prev_song
    
    def set_current_position(self, position: int) -> bool:
        """
        Set the current position in the playlist.
        
        Args:
            position: Position to set as current (0-indexed)
            
        Returns:
            bool: True if position was set successfully, False otherwise
        """
        if self.songs.is_empty():
            return False
        
        if position < 0 or position >= self.songs.size():
            return False
        
        try:
            self.songs.set_current(position)
            self.current_position = position
            return True
        except Exception:
            return False
    
    def shuffle_songs(self) -> None:
        """
        Randomly reorder the songs in the playlist.
        Maintains current song but may change its position.
        """
        if self.songs.size() <= 1:
            return
        
        current_song = self.get_current_song()
        self.songs.shuffle()
        
        # Update current position after shuffle
        if current_song:
            self.current_position = self._find_song_position(current_song.id)
    
    def get_songs_list(self) -> List[Song]:
        """
        Get all songs as a Python list.
        
        Returns:
            List[Song]: List of all songs in the playlist
        """
        return self.songs.to_list()
    
    def move_song(self, from_position: int, to_position: int) -> bool:
        """
        Move a song from one position to another (for drag & drop).
        
        Args:
            from_position: Current position of the song
            to_position: Target position for the song
            
        Returns:
            bool: True if move was successful, False otherwise
        """
        if self.songs.is_empty():
            return False
        
        if (from_position < 0 or from_position >= self.songs.size() or 
            to_position < 0 or to_position >= self.songs.size()):
            return False
        
        try:
            # Update current position if it's affected by the move
            if from_position == self.current_position:
                self.current_position = to_position
            elif from_position < self.current_position <= to_position:
                self.current_position -= 1
            elif to_position <= self.current_position < from_position:
                self.current_position += 1
            
            self.songs.move_to_position(from_position, to_position)
            
            # Update current in the songs list
            if not self.songs.is_empty():
                self.songs.set_current(self.current_position)
            
            return True
            
        except Exception as e:
            print(f"Error moving song: {e}")
            return False
    
    def update_totals(self) -> None:
        """Update total duration and song count."""
        self.song_count = self.songs.size()
        self.total_duration = sum(song.duration for song in self.get_songs_list())
    
    def get_total_duration_formatted(self) -> str:
        """
        Get total duration formatted as HH:MM:SS or MM:SS.
        
        Returns:
            str: Formatted duration string
        """
        total_seconds = int(self.total_duration)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def is_empty(self) -> bool:
        """
        Check if the playlist is empty.
        
        Returns:
            bool: True if playlist has no songs, False otherwise
        """
        return self.songs.is_empty()
    
    def has_next(self) -> bool:
        """
        Check if there is a next song available.
        
        Returns:
            bool: True if there is a next song, False otherwise
        """
        return self.songs.has_next()
    
    def has_previous(self) -> bool:
        """
        Check if there is a previous song available.
        
        Returns:
            bool: True if there is a previous song, False otherwise
        """
        return self.songs.has_previous()
    
    def _find_song_position(self, song_id: str) -> int:
        """
        Find the position of a song by ID.
        
        Args:
            song_id: ID of the song to find
            
        Returns:
            int: Position of the song, or 0 if not found
        """
        current = self.songs.head
        position = 0
        
        while current:
            if current.data.id == song_id:
                return position
            current = current.next
            position += 1
        
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the playlist to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the playlist
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cover_image": self.cover_image,
            "songs": [song.to_dict() for song in self.get_songs_list()],
            "current_position": self.current_position,
            "created_at": self.created_at.isoformat(),
            "total_duration": self.total_duration,
            "song_count": self.song_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Playlist':
        """
        Create a Playlist instance from a dictionary.
        
        Args:
            data: Dictionary containing playlist data
            
        Returns:
            Playlist: New Playlist instance
            
        Raises:
            ValueError: If data is invalid
        """
        if 'name' not in data:
            raise ValueError("Playlist name is required")
        
        # Create playlist with basic info
        playlist = cls(
            name=data['name'],
            description=data.get('description'),
            cover_image=data.get('cover_image'),
            playlist_id=data.get('id')
        )
        
        # Set timestamp if provided
        if 'created_at' in data:
            try:
                playlist.created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            except ValueError:
                pass  # Keep current timestamp if parsing fails
        
        # Add songs
        if 'songs' in data and isinstance(data['songs'], list):
            for song_data in data['songs']:
                try:
                    song = Song.from_dict(song_data)
                    playlist.add_song(song)
                except Exception as e:
                    print(f"Error loading song: {e}")
                    continue
        
        # Set current position
        current_pos = data.get('current_position', 0)
        if not playlist.is_empty() and 0 <= current_pos < playlist.song_count:
            playlist.set_current_position(current_pos)
        
        return playlist
    
    def duplicate(self, new_name: Optional[str] = None) -> 'Playlist':
        """
        Create a duplicate of this playlist.
        
        Args:
            new_name: Optional name for the new playlist
            
        Returns:
            Playlist: New playlist instance with copied songs
        """
        duplicate_name = new_name or f"{self.name} (Copy)"
        
        new_playlist = Playlist(
            name=duplicate_name,
            description=self.description,
            cover_image=self.cover_image
        )
        
        # Add all songs to the new playlist
        for song in self.get_songs_list():
            new_playlist.add_song(song)
        
        return new_playlist
    
    def __str__(self) -> str:
        """String representation of the playlist."""
        return f"{self.name} ({self.song_count} songs, {self.get_total_duration_formatted()})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the playlist."""
        return f"Playlist(id='{self.id[:8]}...', name='{self.name}', songs={self.song_count})"
    
    def __len__(self) -> int:
        """Return the number of songs in the playlist."""
        return self.song_count
    
    def __bool__(self) -> bool:
        """Return True if playlist has songs, False if empty."""
        return not self.is_empty()


# Example usage and testing
if __name__ == "__main__":
    print("Playlist model is ready for use!")
    
    # Example of creating a playlist (commented out since it requires actual Song objects)
    """
    # Create a playlist
    playlist = Playlist("My Awesome Playlist", "Collection of great songs")
    
    # Add songs (would need actual Song objects)
    # playlist.add_song(song1)
    # playlist.add_song(song2)
    
    print(f"Created playlist: {playlist}")
    print(f"Is empty: {playlist.is_empty()}")
    print(f"Total duration: {playlist.get_total_duration_formatted()}")
    """