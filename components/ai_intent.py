"""
AI Intent component for the ECS architecture.
Represents an AI entity's intention for its next action.
"""
from enum import Enum, auto
from typing import Optional, Tuple

class ActionType(Enum):
    """Types of actions an AI can take"""
    NONE = auto()
    MOVE = auto()
    ATTACK = auto()
    WAIT = auto()
    FLEE = auto()
    PATROL = auto()

class AIIntent:
    """Component representing an AI entity's intention for its next action"""
    
    def __init__(self):
        """Initialize with no intent"""
        self.action_type = ActionType.NONE
        self.target_entity: Optional[int] = None
        self.target_position: Optional[Tuple[int, int]] = None
        self.path: list[Tuple[int, int]] = []
        self.state: str = "idle"
        
    def set_move_intent(self, x: int, y: int) -> None:
        """Set intent to move to a specific position"""
        self.action_type = ActionType.MOVE
        self.target_position = (x, y)
        self.target_entity = None
        
    def set_attack_intent(self, target_entity: int) -> None:
        """Set intent to attack a specific entity"""
        self.action_type = ActionType.ATTACK
        self.target_entity = target_entity
        self.target_position = None
        
    def set_wait_intent(self) -> None:
        """Set intent to wait (do nothing)"""
        self.action_type = ActionType.WAIT
        self.target_entity = None
        self.target_position = None
        
    def set_flee_intent(self, from_position: Tuple[int, int]) -> None:
        """Set intent to flee from a position"""
        self.action_type = ActionType.FLEE
        self.target_position = from_position
        self.target_entity = None
        
    def set_patrol_intent(self, path: list[Tuple[int, int]]) -> None:
        """Set intent to patrol along a path"""
        self.action_type = ActionType.PATROL
        self.path = path
        
    def has_intent(self) -> bool:
        """Check if this entity has any intent"""
        return self.action_type != ActionType.NONE
    
    def clear_intent(self) -> None:
        """Clear the current intent"""
        self.action_type = ActionType.NONE
        self.target_entity = None
        self.target_position = None
        
    def __str__(self) -> str:
        return f"AIIntent(action={self.action_type.name})"
