"""
Input System module for the ECS architecture.
Handles player input and translates it into game actions.
"""
import pygame
from enum import Enum, auto
from typing import Dict, Optional, Callable, Any, Set

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.position import Position
from components.player_tag import PlayerTag
from utils.debug import debug_print

class InputAction(Enum):
    """Available input actions for the player"""
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    WAIT = auto()
    ATTACK = auto()
    QUIT = auto()
    INVENTORY = auto()
    PICKUP = auto()
    USE_ITEM = auto()
    EXAMINE = auto()
    TOGGLE_FULLSCREEN = auto()

class InputSystem(System):
    """System responsible for handling player input"""
    
    def __init__(self):
        """Initialize the input system"""
        super().__init__()
        
        # Required components for this system
        self._required_component_types = [PlayerTag, Position]
        
        # Set a very low priority so input is processed first
        self._priority = -100
        
        # Initialize input mapping (key -> action)
        self._input_mapping: Dict[int, InputAction] = {
            pygame.K_UP: InputAction.MOVE_UP,
            pygame.K_DOWN: InputAction.MOVE_DOWN,
            pygame.K_LEFT: InputAction.MOVE_LEFT,
            pygame.K_RIGHT: InputAction.MOVE_RIGHT,
            pygame.K_PERIOD: InputAction.WAIT,
            pygame.K_SPACE: InputAction.ATTACK,
            pygame.K_i: InputAction.INVENTORY,
            pygame.K_g: InputAction.PICKUP,
            pygame.K_u: InputAction.USE_ITEM,
            pygame.K_x: InputAction.EXAMINE,
            pygame.K_ESCAPE: InputAction.QUIT,
            pygame.K_F11: InputAction.TOGGLE_FULLSCREEN
        }
        
        # Additional key mapping for numpad/vi keys
        self._input_mapping.update({
            pygame.K_k: InputAction.MOVE_UP,
            pygame.K_j: InputAction.MOVE_DOWN,
            pygame.K_h: InputAction.MOVE_LEFT,
            pygame.K_l: InputAction.MOVE_RIGHT,
            pygame.K_KP8: InputAction.MOVE_UP,
            pygame.K_KP2: InputAction.MOVE_DOWN,
            pygame.K_KP4: InputAction.MOVE_LEFT,
            pygame.K_KP6: InputAction.MOVE_RIGHT,
        })
        
        # Callbacks for input actions
        self._action_callbacks: Dict[InputAction, Callable] = {}
        
        # Flag indicating if player has taken an action
        self.action_taken = False
        
        # The current action being processed
        self.current_action: Optional[InputAction] = None
        
        # Flag indicating if the game should quit
        self.should_quit = False
    
    def register_action_callback(self, action: InputAction, 
                                callback: Callable[[EntityManager, int], Any]) -> None:
        """
        Register a callback function for a specific input action
        
        Args:
            action: The input action to register a callback for
            callback: The callback function to call when the action is triggered
                     Function signature: callback(entity_manager, player_entity_id)
        """
        self._action_callbacks[action] = callback
    
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Process player input
        
        Args:
            entity_manager: The entity manager containing all entities and components
            dt: Delta time since last update (not used for input)
        """
        # Reset action taken flag
        self.action_taken = False
        self.current_action = None
        
        # Get the player entity
        player_entities = entity_manager.get_entities_with_components(
            [PlayerTag, Position]
        )
        
        # There should be exactly one player entity
        if not player_entities:
            return
        
        player_entity_id = next(iter(player_entities))
        
        # Process pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.should_quit = True
                return
                
            elif event.type == pygame.KEYDOWN:
                # Check if this key is mapped to an action
                if event.key in self._input_mapping:
                    action = self._input_mapping[event.key]
                    self.current_action = action
                    
                    # Call the registered callback if there is one
                    if action in self._action_callbacks:
                        self._action_callbacks[action](entity_manager, player_entity_id)
                        
                    # Mark that an action was taken
                    self.action_taken = True
                    
                    # Special handling for quit action
                    if action == InputAction.QUIT:
                        self.should_quit = True
                        
                    # Don't process more input if an action was taken
                    break
    
    def get_player_entity(self, entity_manager: EntityManager) -> Optional[int]:
        """Get the player entity ID"""
        player_entities = entity_manager.get_entities_with_components([PlayerTag])
        if player_entities:
            return next(iter(player_entities))
        return None
