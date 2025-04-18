"""
UI Component module for the ECS architecture.
Defines base UI components used by the UI system.
"""
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field


class UIComponent:
    """
    Base component for UI elements. All UI elements should extend this.
    Follows ECS principles by storing only data, no behavior.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 visible: bool = True, z_index: int = 0):
        """
        Initialize the UI component
        
        Args:
            x: X position of the UI element (in grid cells)
            y: Y position of the UI element (in grid cells)
            width: Width of the UI element (in grid cells)
            height: Height of the UI element (in grid cells)
            visible: Whether the UI element is visible
            z_index: Rendering order (higher values render on top)
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = visible
        self.z_index = z_index
        # Border and background colors (RGB tuples)
        self.border_color = (200, 200, 200)  # Light gray border
        self.bg_color = (0, 0, 0)  # Black background
        self.has_border = True


class UIWindowComponent(UIComponent):
    """Component representing a window UI element with a title and border"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 title: str = "", visible: bool = True, z_index: int = 0):
        """
        Initialize the UI window component
        
        Args:
            x: X position of the window (in grid cells)
            y: Y position of the window (in grid cells)
            width: Width of the window (in grid cells)
            height: Height of the window (in grid cells)
            title: Title of the window
            visible: Whether the window is visible
            z_index: Rendering order (higher values render on top)
        """
        super().__init__(x, y, width, height, visible, z_index)
        self.title = title
        self.title_color = (255, 255, 255)  # White title text
        

class UIPlayerInfoComponent(UIWindowComponent):
    """Component representing player information UI"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 visible: bool = True, z_index: int = 10):
        """
        Initialize the player info UI component
        
        Args:
            x: X position of the UI element (in grid cells)
            y: Y position of the UI element (in grid cells)
            width: Width of the UI element (in grid cells)
            height: Height of the UI element (in grid cells)
            visible: Whether the UI element is visible
            z_index: Rendering order (higher values render on top)
        """
        super().__init__(x, y, width, height, "Player Info", visible, z_index)
        # Store cached player stats for display
        self.player_name = "Hero"
        self.health_current = 0
        self.health_max = 0
        self.attack = 0
        self.defense = 0
        self.position_x = 0
        self.position_y = 0
        self.turn_count = 0


class UILogComponent(UIWindowComponent):
    """Component representing a message log UI element"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 max_messages: int = 100, visible: bool = True, z_index: int = 10):
        """
        Initialize the log UI component
        
        Args:
            x: X position of the log window (in grid cells)
            y: Y position of the log window (in grid cells)
            width: Width of the log window (in grid cells)
            height: Height of the log window (in grid cells)
            max_messages: Maximum number of messages to store
            visible: Whether the log window is visible
            z_index: Rendering order (higher values render on top)
        """
        super().__init__(x, y, width, height, "Message Log", visible, z_index)
        self.messages: List[Tuple[str, Tuple[int, int, int]]] = []
        self.max_messages = max_messages
        
    def add_message(self, message: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a message to the log with the given color"""
        self.messages.append((message, color))
        # Trim if exceeded max messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
