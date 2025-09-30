import random
from typing import Any, Optional, List


class Node:
    """
    Node class for doubly linked list.
    
    Each node contains data and pointers to both next and previous nodes,
    enabling bidirectional traversal through the playlist.
    """
    
    def __init__(self, data: Any) -> None:
        """
        Initialize a new node.
        
        Args:
            data: The data to store in this node (typically a Song object)
        """
        self.data = data
        self.next: Optional['Node'] = None
        self.prev: Optional['Node'] = None
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"Node({self.data})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the node."""
        return f"Node(data={self.data}, next={self.next.data if self.next else None}, prev={self.prev.data if self.prev else None})"


class DoublyLinkedList:
    """
    Doubly Linked List implementation for music player.
    
    This class provides all necessary operations for managing a playlist
    with bidirectional navigation, essential for prev/next song functionality.
    """
    
    def __init__(self) -> None:
        """Initialize empty doubly linked list."""
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self.current: Optional[Node] = None
        self._size: int = 0
    
    def is_empty(self) -> bool:
        """
        Check if the list is empty.
        
        Returns:
            bool: True if list is empty, False otherwise
        """
        return self.head is None
    
    def size(self) -> int:
        """
        Get the number of elements in the list.
        
        Returns:
            int: Number of elements in the list
        """
        return self._size
    
    def insert_at_beginning(self, data: Any) -> None:
        """
        Insert a new element at the beginning of the list.
        
        Args:
            data: The data to insert
        """
        if data is None:
            raise ValueError("Cannot insert None data")
        
        new_node = Node(data)
        
        if self.is_empty():
            self.head = self.tail = new_node
            self.current = new_node  # Set first song as current
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        
        self._size += 1
    
    def insert_at_end(self, data: Any) -> None:
        """
        Insert a new element at the end of the list.
        
        Args:
            data: The data to insert
        """
        if data is None:
            raise ValueError("Cannot insert None data")
        
        new_node = Node(data)
        
        if self.is_empty():
            self.head = self.tail = new_node
            self.current = new_node  # Set first song as current
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        
        self._size += 1
    
    def insert_at_position(self, data: Any, position: int) -> None:
        """
        Insert a new element at the specified position.
        
        Args:
            data: The data to insert
            position: The position to insert at (0-indexed)
            
        Raises:
            ValueError: If position is invalid or data is None
        """
        if data is None:
            raise ValueError("Cannot insert None data")
        
        if position < 0 or position > self._size:
            raise ValueError(f"Invalid position {position}. Must be between 0 and {self._size}")
        
        if position == 0:
            self.insert_at_beginning(data)
        elif position == self._size:
            self.insert_at_end(data)
        else:
            new_node = Node(data)
            current = self._get_node_at_position(position)
            
            # Insert before current node
            new_node.next = current
            new_node.prev = current.prev
            current.prev.next = new_node
            current.prev = new_node
            
            self._size += 1
    
    def delete_by_value(self, data: Any) -> bool:
        """
        Delete the first occurrence of the specified value.
        
        Args:
            data: The data to delete
            
        Returns:
            bool: True if element was found and deleted, False otherwise
        """
        if self.is_empty():
            return False
        
        current = self.head
        
        while current:
            if current.data == data:
                self._delete_node(current)
                return True
            current = current.next
        
        return False
    
    def delete_at_position(self, position: int) -> Any:
        """
        Delete element at the specified position.
        
        Args:
            position: The position to delete from (0-indexed)
            
        Returns:
            Any: The data that was deleted
            
        Raises:
            ValueError: If position is invalid
            IndexError: If list is empty
        """
        if self.is_empty():
            raise IndexError("Cannot delete from empty list")
        
        if position < 0 or position >= self._size:
            raise ValueError(f"Invalid position {position}. Must be between 0 and {self._size - 1}")
        
        node_to_delete = self._get_node_at_position(position)
        data = node_to_delete.data
        self._delete_node(node_to_delete)
        
        return data
    
    def _delete_node(self, node: Node) -> None:
        """
        Internal method to delete a specific node.
        
        Args:
            node: The node to delete
        """
        # Handle current pointer if deleting current song
        if self.current == node:
            if node.next:
                self.current = node.next
            elif node.prev:
                self.current = node.prev
            else:
                self.current = None
        
        # Update head if necessary
        if node == self.head:
            self.head = node.next
            if self.head:
                self.head.prev = None
        
        # Update tail if necessary
        if node == self.tail:
            self.tail = node.prev
            if self.tail:
                self.tail.next = None
        
        # Update links for middle nodes
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        
        self._size -= 1
    
    def find(self, data: Any) -> Optional[Node]:
        """
        Find the first node containing the specified data.
        
        Args:
            data: The data to search for
            
        Returns:
            Optional[Node]: The node containing the data, or None if not found
        """
        current = self.head
        
        while current:
            if current.data == data:
                return current
            current = current.next
        
        return None
    
    def get_at_position(self, position: int) -> Any:
        """
        Get the data at the specified position.
        
        Args:
            position: The position to get data from (0-indexed)
            
        Returns:
            Any: The data at the specified position
            
        Raises:
            ValueError: If position is invalid
            IndexError: If list is empty
        """
        if self.is_empty():
            raise IndexError("Cannot get from empty list")
        
        if position < 0 or position >= self._size:
            raise ValueError(f"Invalid position {position}. Must be between 0 and {self._size - 1}")
        
        node = self._get_node_at_position(position)
        return node.data
    
    def _get_node_at_position(self, position: int) -> Node:
        """
        Internal method to get node at specified position.
        
        Args:
            position: The position to get node from (0-indexed)
            
        Returns:
            Node: The node at the specified position
        """
        # Optimize by starting from head or tail based on position
        if position <= self._size // 2:
            # Start from head
            current = self.head
            for _ in range(position):
                current = current.next
        else:
            # Start from tail
            current = self.tail
            for _ in range(self._size - 1 - position):
                current = current.prev
        
        return current
    
    def display(self) -> str:
        """
        Get string representation of the entire list.
        
        Returns:
            str: String representation of the list
        """
        if self.is_empty():
            return "[]"
        
        elements = []
        current = self.head
        
        while current:
            marker = " -> *" if current == self.current else ""
            elements.append(f"{current.data}{marker}")
            current = current.next
        
        return " <-> ".join(elements)
    
    def clear(self) -> None:
        """Clear all elements from the list."""
        while not self.is_empty():
            self.delete_at_position(0)
        
        self.head = None
        self.tail = None
        self.current = None
        self._size = 0
    
    def to_list(self) -> List[Any]:
        """
        Convert the doubly linked list to a Python list.
        
        Returns:
            List[Any]: Python list containing all elements
        """
        result = []
        current = self.head
        
        while current:
            result.append(current.data)
            current = current.next
        
        return result
    
    # Music Player Specific Methods
    
    def get_current(self) -> Any:
        """
        Get the data of the current song.
        
        Returns:
            Any: The data of the current song, or None if no current song
        """
        return self.current.data if self.current else None
    
    def get_current_position(self) -> int:
        """
        Get the position of the current song.
        
        Returns:
            int: The position of the current song, or -1 if no current song
        """
        if not self.current:
            return -1
        
        position = 0
        current = self.head
        
        while current and current != self.current:
            position += 1
            current = current.next
        
        return position
    
    def next(self) -> Any:
        """
        Move to the next song in the playlist.
        
        Returns:
            Any: The data of the next song, or None if at end or empty list
        """
        if not self.current or not self.current.next:
            return None
        
        self.current = self.current.next
        return self.current.data
    
    def previous(self) -> Any:
        """
        Move to the previous song in the playlist.
        
        Returns:
            Any: The data of the previous song, or None if at beginning or empty list
        """
        if not self.current or not self.current.prev:
            return None
        
        self.current = self.current.prev
        return self.current.data
    
    def set_current(self, position: int) -> Any:
        """
        Set the current song to the specified position.
        
        Args:
            position: The position to set as current (0-indexed)
            
        Returns:
            Any: The data of the song at the specified position
            
        Raises:
            ValueError: If position is invalid
            IndexError: If list is empty
        """
        if self.is_empty():
            raise IndexError("Cannot set current on empty list")
        
        if position < 0 or position >= self._size:
            raise ValueError(f"Invalid position {position}. Must be between 0 and {self._size - 1}")
        
        self.current = self._get_node_at_position(position)
        return self.current.data
    
    def shuffle(self) -> None:
        """
        Randomly reorder the playlist while maintaining the doubly linked structure.
        The current song remains as current but may change position.
        """
        if self._size <= 1:
            return
        
        # Convert to list, shuffle, and rebuild
        data_list = self.to_list()
        current_data = self.get_current()
        
        random.shuffle(data_list)
        
        # Rebuild the list
        self.clear()
        for data in data_list:
            self.insert_at_end(data)
        
        # Restore current pointer
        if current_data is not None:
            current_node = self.find(current_data)
            if current_node:
                self.current = current_node
    
    def has_next(self) -> bool:
        """
        Check if there is a next song available.
        
        Returns:
            bool: True if there is a next song, False otherwise
        """
        return self.current is not None and self.current.next is not None
    
    def has_previous(self) -> bool:
        """
        Check if there is a previous song available.
        
        Returns:
            bool: True if there is a previous song, False otherwise
        """
        return self.current is not None and self.current.prev is not None
    
    def move_to_position(self, from_pos: int, to_pos: int) -> None:
        """
        Move a song from one position to another (for drag & drop reordering).
        
        Args:
            from_pos: The current position of the song (0-indexed)
            to_pos: The target position for the song (0-indexed)
            
        Raises:
            ValueError: If positions are invalid
            IndexError: If list is empty
        """
        if self.is_empty():
            raise IndexError("Cannot move in empty list")
        
        if from_pos < 0 or from_pos >= self._size or to_pos < 0 or to_pos >= self._size:
            raise ValueError("Invalid position for move operation")
        
        if from_pos == to_pos:
            return
        
        # Get the data to move
        data = self.delete_at_position(from_pos)
        
        # Adjust target position if necessary
        if to_pos > from_pos:
            to_pos -= 1
        
        # Insert at new position
        self.insert_at_position(data, to_pos)


# Example usage and testing
if __name__ == "__main__":
    # Create a playlist
    playlist = DoublyLinkedList()
    
    # Add some songs
    songs = ["Song 1", "Song 2", "Song 3", "Song 4", "Song 5"]
    for song in songs:
        playlist.insert_at_end(song)
    
    print("Playlist:", playlist.display())
    print(f"Current song: {playlist.get_current()}")
    print(f"Size: {playlist.size()}")
    
    # Navigate through songs
    print(f"Next: {playlist.next()}")
    print(f"Next: {playlist.next()}")
    print(f"Previous: {playlist.previous()}")
    
    print("Final playlist:", playlist.display())