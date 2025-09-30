import json
import os
from typing import List, Optional, Dict, Any
from models.playlist import Playlist
from models.song import Song
from patterns.singleton import MusicPlayerManager


class PlaylistService:
    """
    Service for managing playlist operations.
    
    This class provides comprehensive playlist management including
    CRUD operations, song management, search functionality, and
    JSON-based persistence.
    """
    
    def __init__(self, data_directory: str = "data"):
        self.data_directory = data_directory
        self.playlists_file = os.path.join(data_directory, "playlists.json")
        self.playlists: List[Playlist] = []
        self.player_manager = MusicPlayerManager.get_instance()
        
        os.makedirs(data_directory, exist_ok=True)
        
        # Solo cargar si la lista está vacía (para evitar sobrescribir datos en memoria)
        if not self.playlists:
            self.load_playlists_from_file()
    
    # PLAYLIST CRUD OPERATIONS
    
    def create_playlist(self, name: str, description: str = "") -> Playlist:
        """
        Create a new playlist.
        
        Args:
            name: Name of the playlist
            description: Optional description
            
        Returns:
            Playlist: Created playlist object
            
        Raises:
            ValueError: If playlist name already exists or is invalid
        """
        if not name or not name.strip():
            raise ValueError("Playlist name cannot be empty")
        
        name = name.strip()
        
        # Check for duplicate names
        if self._is_playlist_name_exists(name):
            raise ValueError(f"Playlist with name '{name}' already exists")
        
        playlist = Playlist(name=name, description=description)
        self.playlists.append(playlist)
        self.save_playlists_to_file()
        
        return playlist
    
    def get_all_playlists(self) -> List[Playlist]:
        """
        Get all playlists.
        
        Returns:
            List[Playlist]: List of all playlists
        """
        return self.playlists.copy()
    
    def get_playlist_by_id(self, playlist_id: str) -> Optional[Playlist]:
        """
        Get a playlist by its ID - VERSIÓN CON DIAGNÓSTICO COMPLETO.
        """
        print(f"[PLAYLIST.get_by_id] ===== BÚSQUEDA DE PLAYLIST =====")
        print(f"[PLAYLIST.get_by_id] ID solicitado: '{playlist_id}'")
        print(f"[PLAYLIST.get_by_id] Tipo: {type(playlist_id)}")
        print(f"[PLAYLIST.get_by_id] Longitud: {len(playlist_id) if playlist_id else 'None'}")
        print(f"[PLAYLIST.get_by_id] Repr: {repr(playlist_id)}")
        
        if not playlist_id:
            print(f"[PLAYLIST.get_by_id] ERROR: playlist_id está vacío")
            return None
        
        # Limpiar el ID
        clean_id = playlist_id.strip()
        print(f"[PLAYLIST.get_by_id] ID limpio: '{clean_id}'")
        
        print(f"[PLAYLIST.get_by_id] Total playlists para buscar: {len(self.playlists)}")
        
        # Verificar que self.playlists no esté vacío
        if not self.playlists:
            print(f"[PLAYLIST.get_by_id] CRÍTICO: self.playlists está vacío")
            return None
        
        # Buscar con diagnóstico detallado
        for i, playlist in enumerate(self.playlists):
            print(f"[PLAYLIST.get_by_id] --- Playlist {i} ---")
            print(f"[PLAYLIST.get_by_id] ID en playlist: '{playlist.id}'")
            print(f"[PLAYLIST.get_by_id] Nombre: '{playlist.name}'")
            print(f"[PLAYLIST.get_by_id] Tipo ID playlist: {type(playlist.id)}")
            print(f"[PLAYLIST.get_by_id] Longitud ID playlist: {len(playlist.id)}")
            print(f"[PLAYLIST.get_by_id] Repr ID playlist: {repr(playlist.id)}")
            
            # Múltiples tipos de comparación
            exact_match = playlist.id == clean_id
            strip_match = playlist.id.strip() == clean_id.strip()
            lower_match = playlist.id.lower() == clean_id.lower()
            
            print(f"[PLAYLIST.get_by_id] Comparaciones:")
            print(f"[PLAYLIST.get_by_id]   Exacta: {exact_match}")
            print(f"[PLAYLIST.get_by_id]   Strip: {strip_match}")
            print(f"[PLAYLIST.get_by_id]   Lower: {lower_match}")
            
            if exact_match:
                print(f"[PLAYLIST.get_by_id] ✅ ENCONTRADO por coincidencia exacta: {playlist.name}")
                return playlist
            elif strip_match:
                print(f"[PLAYLIST.get_by_id] ✅ ENCONTRADO por strip: {playlist.name}")
                return playlist
            elif lower_match:
                print(f"[PLAYLIST.get_by_id] ✅ ENCONTRADO por lower: {playlist.name}")
                return playlist
        
        print(f"[PLAYLIST.get_by_id] ❌ NO ENCONTRADO")
        print(f"[PLAYLIST.get_by_id] IDs disponibles:")
        for p in self.playlists:
            print(f"[PLAYLIST.get_by_id]   - '{p.id}'")
        
        return None
    
    def update_playlist(self, playlist_id: str, name: str, description: str = "") -> bool:
        """
        Update playlist information.
        
        Args:
            playlist_id: ID of playlist to update
            name: New name for the playlist
            description: New description
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return False
        
        if not name or not name.strip():
            return False
        
        name = name.strip()
        
        # Check for duplicate names (excluding current playlist)
        for other_playlist in self.playlists:
            if other_playlist.id != playlist_id and other_playlist.name.lower() == name.lower():
                return False
        
        playlist.name = name
        playlist.description = description.strip() if description else None
        self.save_playlists_to_file()
        
        return True
    
    # En playlist_service.py, reemplaza el método delete_playlist
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist - VERSIÓN CON DEBUG.
        
        Args:
            playlist_id: ID of playlist to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            print(f"[PLAYLIST_SERVICE] ===== DELETE PLAYLIST =====")
            print(f"[PLAYLIST_SERVICE] Deleting playlist: {playlist_id}")
            print(f"[PLAYLIST_SERVICE] Current playlists: {len(self.playlists)}")
            
            playlist = self.get_playlist_by_id(playlist_id)
            if playlist is None:
                print(f"[PLAYLIST_SERVICE] Playlist not found: {playlist_id}")
                return False
            
            print(f"[PLAYLIST_SERVICE] Found playlist to delete: {playlist.name}")
            
            # If this is the current playlist, clear it from player manager
            if (self.player_manager.current_playlist and 
                self.player_manager.current_playlist.id == playlist_id):
                print(f"[PLAYLIST_SERVICE] Clearing current playlist from player manager")
                self.player_manager.reset_state()
            
            # Remove from list
            print(f"[PLAYLIST_SERVICE] Removing from playlists list...")
            self.playlists.remove(playlist)
            print(f"[PLAYLIST_SERVICE] Removed. Now have {len(self.playlists)} playlists")
            
            # Save to file
            print(f"[PLAYLIST_SERVICE] Saving to file...")
            save_success = self.save_playlists_to_file()
            print(f"[PLAYLIST_SERVICE] Save result: {save_success}")
            
            if not save_success:
                print(f"[PLAYLIST_SERVICE] WARNING: Could not save to file")
                # Note: We don't return False here because the playlist was removed from memory
                # The user can try saving again later
            
            print(f"[PLAYLIST_SERVICE] ===== DELETE COMPLETED =====")
            return True
            
        except ValueError as e:
            # This happens if playlist is not in the list
            print(f"[PLAYLIST_SERVICE] ValueError (playlist not in list): {e}")
            return False
        except Exception as e:
            print(f"[PLAYLIST_SERVICE] Error deleting playlist: {e}")
            import traceback
            traceback.print_exc()
            return False


    def add_song_to_playlist(self, playlist_id: str, song: Song, position: Optional[int] = None) -> bool:
        """VERSIÓN FINAL CORREGIDA - El problema estaba en la lógica del bucle"""
        try:
            print(f"[PLAYLIST] === add_song_to_playlist INICIADO ===")
            print(f"[PLAYLIST] Playlist ID: '{playlist_id}'")
            print(f"[PLAYLIST] Song: {song.title if song else 'None'}")
            
            # PASO 1: Validaciones básicas
            if not playlist_id or not playlist_id.strip():
                print(f"[PLAYLIST] ERROR: playlist_id vacío")
                return False
                
            if not isinstance(song, Song):
                print(f"[PLAYLIST] ERROR: song no es Song: {type(song)}")
                return False
            
            playlist_id = playlist_id.strip()
            
            # PASO 2: Buscar playlist - LÓGICA CORREGIDA
            playlist = None
            print(f"[PLAYLIST] Buscando playlist directamente...")
            
            for i, p in enumerate(self.playlists):
                print(f"[PLAYLIST] Playlist {i}: ID='{p.id}', Name='{p.name}'")
                if p.id == playlist_id:
                    playlist = p
                    print(f"[PLAYLIST] ✅ ENCONTRADO: {p.name}")
                    break  # CRÍTICO: Este break debe funcionar
            else:
                # Este bloque se ejecuta si el for termina sin break
                print(f"[PLAYLIST] ❌ NO ENCONTRADO en búsqueda directa")
            
            # Verificar si encontramos el playlist
            if playlist is None:
                print(f"[PLAYLIST] CRÍTICO: playlist es None después de la búsqueda")
                return False
            
            # PASO 3: Verificar el playlist encontrado
            print(f"[PLAYLIST] Playlist encontrada: {playlist.name}")
            print(f"[PLAYLIST] Songs actuales: {playlist.song_count}")
            
            # PASO 4: Agregar la canción
            print(f"[PLAYLIST] Llamando playlist.add_song...")
            
            success = playlist.add_song(song, position)
            print(f"[PLAYLIST] playlist.add_song retornó: {success}")
            
            if not success:
                print(f"[PLAYLIST] ERROR: add_song retornó False")
                return False
            
            # PASO 5: Verificar que se agregó
            print(f"[PLAYLIST] Songs después de agregar: {playlist.song_count}")
            
            # PASO 6: Guardar
            print(f"[PLAYLIST] Guardando al archivo...")
            save_success = self.save_playlists_to_file()
            print(f"[PLAYLIST] save_playlists_to_file retornó: {save_success}")
            
            print(f"[PLAYLIST] === ÉXITO COMPLETO ===")
            return True
            
        except Exception as e:
            print(f"[PLAYLIST] EXCEPCIÓN GENERAL: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def remove_song_from_playlist(self, playlist_id: str, song_id: str) -> bool:
        """
        Remove a song from a playlist.
        
        Args:
            playlist_id: ID of the playlist
            song_id: ID of the song to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return False
        
        success = playlist.remove_song(song_id)
        if success:
            self.save_playlists_to_file()
        
        return success
    
    def move_song_in_playlist(self, playlist_id: str, from_pos: int, to_pos: int) -> bool:
        """
        Move a song within a playlist.
        
        Args:
            playlist_id: ID of the playlist
            from_pos: Current position of the song
            to_pos: Target position for the song
            
        Returns:
            bool: True if moved successfully, False otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return False
        
        success = playlist.move_song(from_pos, to_pos)
        if success:
            self.save_playlists_to_file()
        
        return success
    
    def shuffle_playlist(self, playlist_id: str) -> bool:
        """
        Shuffle songs in a playlist.
        
        Args:
            playlist_id: ID of the playlist to shuffle
            
        Returns:
            bool: True if shuffled successfully, False otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return False
        
        playlist.shuffle_songs()
        self.save_playlists_to_file()
        
        return True
    
    # PLAYBACK OPERATIONS
    
    def set_current_playlist(self, playlist_id: str) -> bool:
        """
        Set a playlist as the current active playlist.
        
        Args:
            playlist_id: ID of the playlist to set as current
            
        Returns:
            bool: True if set successfully, False otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return False
        
        try:
            self.player_manager.set_current_playlist(playlist)
            return True
        except Exception:
            return False
    
    def next_song_in_playlist(self, playlist_id: str) -> Optional[Song]:
        """
        Move to next song in a playlist.
        
        Args:
            playlist_id: ID of the playlist
            
        Returns:
            Optional[Song]: Next song if available, None otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return None
        
        return playlist.next_song()
    
    def previous_song_in_playlist(self, playlist_id: str) -> Optional[Song]:
        """
        Move to previous song in a playlist.
        
        Args:
            playlist_id: ID of the playlist
            
        Returns:
            Optional[Song]: Previous song if available, None otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return None
        
        return playlist.previous_song()
    
    def jump_to_song(self, playlist_id: str, position: int) -> Optional[Song]:
        """
        Jump to a specific song position in a playlist.
        
        Args:
            playlist_id: ID of the playlist
            position: Position to jump to (0-indexed)
            
        Returns:
            Optional[Song]: Song at the position if valid, None otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return None
        
        if playlist.set_current_position(position):
            return playlist.get_current_song()
        
        return None
    
    # SEARCH FUNCTIONALITY
    
    def search_playlists(self, query: str) -> List[Playlist]:
        """
        Search playlists by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List[Playlist]: List of matching playlists
        """
        if not query or not query.strip():
            return []
        
        query = query.strip().lower()
        results = []
        
        for playlist in self.playlists:
            # Search in name
            if query in playlist.name.lower():
                results.append(playlist)
                continue
            
            # Search in description
            if playlist.description and query in playlist.description.lower():
                results.append(playlist)
        
        return results
    
    def search_songs_in_playlist(self, playlist_id: str, query: str) -> List[Song]:
        """
        Search songs within a specific playlist.
        
        Args:
            playlist_id: ID of the playlist to search in
            query: Search query string
            
        Returns:
            List[Song]: List of matching songs
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist or not query or not query.strip():
            return []
        
        query = query.strip().lower()
        results = []
        
        for song in playlist.get_songs_list():
            # Search in title
            if query in song.title.lower():
                results.append(song)
                continue
            
            # Search in artist
            if song.artist and query in song.artist.lower():
                results.append(song)
                continue
            
            # Search in album
            if song.album and query in song.album.lower():
                results.append(song)
        
        return results
    
    # PERSISTENCE OPERATIONS
    def save_playlists_to_file(self, file_path: Optional[str] = None) -> bool:
        target_file = file_path or self.playlists_file
        
        try:
            print(f"[PLAYLIST] Saving {len(self.playlists)} playlists to {target_file}")
            
            # Estructura correcta del JSON
            data_to_save = {
                "playlists": [playlist.to_dict() for playlist in self.playlists]
            }
            
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[PLAYLIST] Successfully saved {len(self.playlists)} playlists")
            return True
            
        except Exception as e:
            print(f"[PLAYLIST] Error saving playlists: {e}")
            return False
        
        # En playlist_service.py, reemplaza el método load_playlists_from_file
    def load_playlists_from_file(self, file_path: Optional[str] = None) -> bool:
        target_file = file_path or self.playlists_file
        
        if not os.path.exists(target_file):
            print(f"[PLAYLIST] No existing file found at {target_file}, starting with empty list")
            return True
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.playlists = []
            
            # Manejar ambos formatos por compatibilidad
            if isinstance(data, list):
                playlists_data = data
            elif isinstance(data, dict) and "playlists" in data:
                playlists_data = data["playlists"]
            else:
                print(f"[PLAYLIST] Invalid data format in {target_file}")
                return False
            
            print(f"[PLAYLIST] Loading {len(playlists_data)} playlists from file")
            
            for i, playlist_dict in enumerate(playlists_data):
                try:
                    print(f"[PLAYLIST] Loading playlist {i}: {playlist_dict.get('name', 'NO_NAME')}")
                    playlist = Playlist.from_dict(playlist_dict)
                    
                    # CRÍTICO: Verificar que el objeto se creó correctamente
                    if not hasattr(playlist, 'name') or playlist.name is None:
                        print(f"[PLAYLIST] ERROR: Playlist {i} tiene name=None")
                        print(f"[PLAYLIST] Playlist dict: {playlist_dict}")
                        continue
                    
                    print(f"[PLAYLIST] Successfully loaded: ID={playlist.id}, Name={playlist.name}")
                    self.playlists.append(playlist)
                    
                except Exception as e:
                    print(f"[PLAYLIST] Error loading playlist {i}: {e}")
                    print(f"[PLAYLIST] Playlist data: {playlist_dict}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"[PLAYLIST] Successfully loaded {len(self.playlists)} playlists")
            
            # Verificar que todos los playlists tienen nombres válidos
            for i, p in enumerate(self.playlists):
                if not hasattr(p, 'name') or p.name is None:
                    print(f"[PLAYLIST] WARNING: Playlist {i} has invalid name: {getattr(p, 'name', 'NO_ATTR')}")
            
            return True
            
        except Exception as e:
            print(f"[PLAYLIST] Error loading playlists: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_playlist_count(self) -> int:
        """Get total number of playlists."""
        return len(self.playlists)
    
    def get_total_songs_count(self) -> int:
        """Get total number of songs across all playlists."""
        return sum(playlist.song_count for playlist in self.playlists)
    
    def validate_playlist_songs(self, playlist_id: str) -> Dict[str, Any]:
        """
        Validate that all songs in a playlist still exist.
        
        Args:
            playlist_id: ID of playlist to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return {"valid": False, "error": "Playlist not found"}
        
        valid_songs = []
        invalid_songs = []
        
        for song in playlist.get_songs_list():
            if song.is_valid_file():
                valid_songs.append(song.id)
            else:
                invalid_songs.append({
                    "id": song.id,
                    "title": song.title,
                    "file_path": song.file_path
                })
        
        return {
            "valid": len(invalid_songs) == 0,
            "total_songs": playlist.song_count,
            "valid_songs": len(valid_songs),
            "invalid_songs": invalid_songs
        }
    
    def duplicate_playlist(self, playlist_id: str, new_name: Optional[str] = None) -> Optional[Playlist]:
        """
        Create a duplicate of an existing playlist.
        
        Args:
            playlist_id: ID of playlist to duplicate
            new_name: Optional name for the duplicate
            
        Returns:
            Optional[Playlist]: Duplicated playlist if successful, None otherwise
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return None
        
        try:
            duplicate = playlist.duplicate(new_name)
            
            # Ensure unique name
            original_name = duplicate.name
            counter = 1
            while self._is_playlist_name_exists(duplicate.name):
                duplicate.name = f"{original_name} ({counter})"
                counter += 1
            
            self.playlists.append(duplicate)
            self.save_playlists_to_file()
            
            return duplicate
            
        except Exception:
            return None
    
    def _is_playlist_name_exists(self, name: str) -> bool:
        """Check if a playlist name already exists."""
        return any(playlist.name.lower() == name.lower() for playlist in self.playlists)
    
    def cleanup_invalid_songs(self, playlist_id: str) -> int:
        """
        Remove invalid songs from a playlist.
        
        Args:
            playlist_id: ID of playlist to clean
            
        Returns:
            int: Number of songs removed
        """
        playlist = self.get_playlist_by_id(playlist_id)
        if not playlist:
            return 0
        
        removed_count = 0
        songs_to_remove = []
        
        for song in playlist.get_songs_list():
            if not song.is_valid_file():
                songs_to_remove.append(song.id)
        
        for song_id in songs_to_remove:
            if playlist.remove_song(song_id):
                removed_count += 1
        
        if removed_count > 0:
            self.save_playlists_to_file()
        
        return removed_count


# Example usage
if __name__ == "__main__":
    print("Playlist Service ready for managing playlists!")
    
    # Example usage (commented out since it requires actual setup)
    """
    service = PlaylistService()
    
    # Create a playlist
    playlist = service.create_playlist("My Favorites", "Best songs collection")
    print(f"Created playlist: {playlist}")
    
    # Add songs (would need actual Song objects)
    # service.add_song_to_playlist(playlist.id, song1)
    # service.add_song_to_playlist(playlist.id, song2)
    
    # Search playlists
    results = service.search_playlists("favorites")
    print(f"Search results: {len(results)} playlists found")
    """

    def save_playlists_to_file(self, file_path: Optional[str] = None) -> bool:
        target_file = file_path or self.playlists_file
        
        try:
            print(f"[PLAYLIST] Saving {len(self.playlists)} playlists to {target_file}")
            
            # Estructura correcta del JSON
            data_to_save = {
                "playlists": [playlist.to_dict() for playlist in self.playlists]
            }
            
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False, default=str)
            
            # VERIFICACIÓN ADICIONAL
            if os.path.exists(target_file):
                file_size = os.path.getsize(target_file)
                print(f"[PLAYLIST] File written successfully. Size: {file_size} bytes")
                
                # Leer de vuelta para verificar
                with open(target_file, 'r', encoding='utf-8') as f:
                    verification_data = json.load(f)
                print(f"[PLAYLIST] Verification: file contains {len(verification_data.get('playlists', []))} playlists")
                return True
            else:
                print(f"[PLAYLIST] ERROR: File was not created")
                return False
            
        except Exception as e:
            print(f"[PLAYLIST] Error saving playlists: {e}")
            import traceback
            traceback.print_exc()
            return False