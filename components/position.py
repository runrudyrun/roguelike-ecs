"""
Position component for the ECS architecture.
Represents the position of an entity in the game world.
"""
from typing import Tuple

class Position:
    """Component representing a position in the 2D world grid"""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def get_position(self) -> Tuple[int, int]:
        """Get the position as a tuple (x, y)"""
        return (self.x, self.y)
    
    def set_position(self, x: int, y: int) -> None:
        """Set the position to new coordinates"""
        self.x = x
        self.y = y
    
    def move(self, dx: int, dy: int) -> None:
        """Move the position by a delta amount"""
        self.x += dx
        self.y += dy
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y
    
    def __str__(self) -> str:
        return f"Position(x={self.x}, y={self.y})"
