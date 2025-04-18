"""
TurnState component for the ECS architecture.
Tracks which entities can act in the current turn.
"""
from enum import Enum

class TurnState:
    """Component representing an entity's turn state"""
    
    def __init__(self, can_act: bool = False):
        """
        Initialize the turn state
        
        Args:
            can_act: Whether this entity can act in the current turn
        """
        self.can_act = can_act
    
    def set_can_act(self, can_act: bool) -> None:
        """Set whether this entity can act"""
        self.can_act = can_act
