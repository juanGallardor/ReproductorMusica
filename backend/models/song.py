import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field, validator, root_validator


class Song(BaseModel):
    """
    Song model representing an audio file with metadata.
    
    This class uses Pydantic for automatic validation and serialization,
    ensuring data integrity throughout the music player application.
    """
    
    # Required fields
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the song")
    filename: str = Field(..., min_length=1, description="Original filename of the audio file")
    file_path: str = Field(..., min_length=1, description="Full path to the audio file")
    title: str = Field(..., min_length=1, description="Display title of the song")
    duration: float = Field(..., ge=0, description="Duration of the song in seconds")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    format: str = Field(..., description="Audio format (mp3, wav, flac)")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp when song was added")
    
    # Optional fields
    artist: Optional[str] = Field(None, description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    year: Optional[int] = Field(None, ge=1800, le=2100, description="Release year")
    cover_image: Optional[str] = Field(None, description="Path to cover image file")
    play_count: int = Field(default=0, ge=0, description="Number of times the song has been played")
    
    # Valid audio formats
    VALID_FORMATS: ClassVar[set] = {"mp3", "wav", "flac"}
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "filename": "awesome_song.mp3",
                "file_path": "/music/awesome_song.mp3",
                "title": "Awesome Song",
                "artist": "Great Artist",
                "album": "Best Album",
                "duration": 240.5,
                "file_size": 8420352,
                "format": "mp3",
                "year": 2023,
                "play_count": 5
            }
        }
    
    @validator('format')
    def validate_format(cls, v):
        """
        Validate that the audio format is supported.
        
        Args:
            v: The format value to validate
            
        Returns:
            str: The validated format in lowercase
            
        Raises:
            ValueError: If format is not supported
        """
        if v.lower() not in cls.VALID_FORMATS:
            raise ValueError(f'Format must be one of: {", ".join(cls.VALID_FORMATS)}')
        return v.lower()
    
    @validator('file_path')
    def validate_file_path(cls, v):
        """
        Validate that the file path exists.
        
        Args:
            v: The file path to validate
            
        Returns:
            str: The validated file path
            
        Raises:
            ValueError: If file does not exist
        """
        if not os.path.exists(v):
            raise ValueError(f'File does not exist: {v}')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """
        Validate that the title is not empty after stripping whitespace.
        
        Args:
            v: The title to validate
            
        Returns:
            str: The validated and cleaned title
            
        Raises:
            ValueError: If title is empty or only whitespace
        """
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('artist', 'album')
    def validate_optional_strings(cls, v):
        """
        Validate optional string fields, ensuring they're not just whitespace.
        
        Args:
            v: The string value to validate
            
        Returns:
            str or None: The validated string or None if empty
        """
        if v is not None:
            v = v.strip()
            return v if v else None
        return v
    
    @validator('cover_image')
    def validate_cover_image(cls, v):
        """
        Validate cover image path if provided.
        
        Args:
            v: The cover image path to validate
            
        Returns:
            str or None: The validated path or None
            
        Raises:
            ValueError: If path is provided but file doesn't exist
        """
        if v is not None:
            v = v.strip()
            if v and not os.path.exists(v):
                raise ValueError(f'Cover image file does not exist: {v}')
            return v if v else None
        return v
        
    @root_validator(skip_on_failure=True)
    def validate_filename_matches_path(cls, values):
        """
        Validate that filename matches the actual file in the path.
        
        Args:
            values: Dictionary of all field values
            
        Returns:
            dict: Validated values
            
        Raises:
            ValueError: If filename doesn't match the actual file
        """
        file_path = values.get('file_path')
        filename = values.get('filename')
        
        if file_path and filename:
            actual_filename = os.path.basename(file_path)
            if actual_filename != filename:
                raise ValueError(f'Filename "{filename}" does not match file path "{file_path}"')
        
        return values
    
    @classmethod
    def generate_id(cls) -> str:
        """
        Generate a unique UUID for a new song.
        
        Returns:
            str: A new UUID string
        """
        return str(uuid.uuid4())
    
    def update_metadata(self, title: Optional[str] = None, 
                       artist: Optional[str] = None, 
                       album: Optional[str] = None,
                       year: Optional[int] = None) -> None:
        """
        Update song metadata fields.
        
        Args:
            title: New title for the song
            artist: New artist name
            album: New album name
            year: New release year
        """
        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty")
            self.title = title.strip()
        
        if artist is not None:
            self.artist = artist.strip() if artist.strip() else None
        
        if album is not None:
            self.album = album.strip() if album.strip() else None
            
        if year is not None:
            if year < 1800 or year > 2100:
                raise ValueError("Year must be between 1800 and 2100")
            self.year = year
    
    def increment_play_count(self) -> int:
        """
        Increment the play count for this song.
        
        Returns:
            int: The new play count
        """
        self.play_count += 1
        return self.play_count
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the song to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the song
        """
        data = self.dict()
        # Convert datetime to ISO string for JSON serialization
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Song':
        """
        Create a Song instance from a dictionary.
        
        Args:
            data: Dictionary containing song data
            
        Returns:
            Song: New Song instance
            
        Raises:
            ValueError: If data is invalid
        """
        # Convert ISO string back to datetime if needed
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, use current time
                data['created_at'] = datetime.now()
        
        return cls(**data)
    
    def get_display_name(self) -> str:
        """
        Get a user-friendly display name for the song.
        
        Returns:
            str: Display name in format "Artist - Title" or just "Title"
        """
        if self.artist:
            return f"{self.artist} - {self.title}"
        return self.title
    
    def get_duration_formatted(self) -> str:
        """
        Get duration formatted as MM:SS.
        
        Returns:
            str: Formatted duration string
        """
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_file_size_formatted(self) -> str:
        """
        Get file size formatted in human-readable format.
        
        Returns:
            str: Formatted file size (e.g., "8.4 MB")
        """
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
    
    def is_valid_file(self) -> bool:
        """
        Check if the song file still exists and is accessible.
        
        Returns:
            bool: True if file exists and is accessible, False otherwise
        """
        return os.path.exists(self.file_path) and os.path.isfile(self.file_path)
    
    def get_file_extension(self) -> str:
        """
        Get the file extension from the filename.
        
        Returns:
            str: File extension (e.g., ".mp3")
        """
        return os.path.splitext(self.filename)[1].lower()
    
    def __str__(self) -> str:
        """String representation of the song."""
        return self.get_display_name()
    
    def __repr__(self) -> str:
        """Detailed string representation of the song."""
        return f"Song(id='{self.id[:8]}...', title='{self.title}', artist='{self.artist}', format='{self.format}')"
    
    def __eq__(self, other) -> bool:
        """Compare songs by ID."""
        if not isinstance(other, Song):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on song ID."""
        return hash(self.id)


# Example usage and testing
if __name__ == "__main__":
    # Example of creating a song
    try:
        # Note: In real usage, you'd provide actual file paths
        song_data = {
            "filename": "example.mp3",
            "file_path": "/path/to/example.mp3",  # This would need to be a real path
            "title": "Example Song",
            "artist": "Example Artist",
            "album": "Example Album",
            "duration": 210.5,
            "file_size": 8420352,
            "format": "mp3",
            "year": 2023
        }
        
        # Create song from dictionary
        # song = Song.from_dict(song_data)
        # print(f"Created song: {song}")
        # print(f"Display name: {song.get_display_name()}")
        # print(f"Duration: {song.get_duration_formatted()}")
        # print(f"File size: {song.get_file_size_formatted()}")
        
        print("Song model is ready for use!")
        print("Note: File path validation is enabled - provide real file paths when creating songs.")
        
    except Exception as e:
        print(f"Example error (expected with dummy paths): {e}")