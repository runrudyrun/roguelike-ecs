"""
Renderable component for the ECS architecture.
Describes how an entity should be rendered in the game.
"""
from typing import Tuple

class Renderable:
    """Component representing how an entity should be rendered"""
    
    def __init__(self, 
                 char: str, 
                 color: Tuple[int, int, int] = (255, 255, 255),
                 bg_color: Tuple[int, int, int] = (0, 0, 0),
                 render_priority: int = 0):
        """
        Initialize a renderable component
        
        Args:
            char: The ASCII character to represent this entity
            color: RGB tuple for the foreground color
            bg_color: RGB tuple for the background color
            render_priority: Higher priority entities render on top of lower ones
        """
        self.char = char[0] if len(char) > 0 else '@'  # Use first char only
        self.color = color
        self.bg_color = bg_color
        self.render_priority = render_priority
        self.visible = True
    
    def set_visible(self, visible: bool) -> None:
        """Set whether this entity is visible"""
        self.visible = visible
    
    def __str__(self) -> str:
        return f"Renderable(char='{self.char}', color={self.color})"
