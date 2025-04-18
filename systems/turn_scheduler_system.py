"""
Turn Scheduler System module for the ECS architecture.
Manages the turn counting and game state.
"""
from enum import Enum
from typing import List, Dict, Set, Optional

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.health import Health
from components.player_tag import PlayerTag
from systems.input_system import InputSystem
from utils.debug import debug_print

class GameState(Enum):
    """Possible states of the game"""
    ACTIVE = 0  # Game is active
    GAME_OVER = 1  # Game is over

class TurnSchedulerSystem(System):
    """
    Simple turn scheduler system - just tracks turn count and game state
    No longer manages entity-by-entity turn state
    """
    
    def __init__(self, input_system: InputSystem):
        """
        Initialize the turn scheduler system
        
        Args:
            input_system: Reference to the input system for tracking player actions
        """
        super().__init__()
        
        # No longer needs a special priority since turn management is in GameLoop
        self._priority = 0
        
        # Reference to the input system
        self._input_system = input_system
        
        # Current game state
        self._game_state = GameState.ACTIVE
        
        # Current turn number
        self._turn_number = 0
    
    @property
    def game_state(self) -> GameState:
        """Get the current game state"""
        return self._game_state
    
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        This system no longer manages per-entity turns as that's handled by GameLoop.
        It just checks for game-over conditions.
        
        Args:
            entity_manager: The entity manager
            dt: Delta time since last update
        """
        debug_print("TurnScheduler", f"Current game state: {self._game_state}, Turn: {self._turn_number}")
        
        # Handle different game states
        if self._game_state == GameState.GAME_OVER:
            # Game is over, nothing to do
            debug_print("TurnScheduler", "Game over state, no turn processing")
            return
        
        # Get the player entity
        player_entities = entity_manager.get_entities_with_components([PlayerTag])
        if not player_entities:
            debug_print("TurnScheduler", "No player entity found")
            return
        
        player_id = next(iter(player_entities))
        
        # Check for game over condition
        player_health = entity_manager.get_component(player_id, Health)
        if player_health and not player_health.is_alive():
            debug_print("TurnScheduler", "Player has died, game over")
            self._game_state = GameState.GAME_OVER
    
    def advance_turn(self) -> None:
        """
        Advance to the next game turn
        """
        self._turn_number += 1
        debug_print("TurnScheduler", f"Advanced to turn {self._turn_number}")
    
    @property
    def turn_number(self) -> int:
        """Get the current turn number"""
        return self._turn_number
    
    def set_game_over(self) -> None:
        """Set the game state to game over"""
        self._game_state = GameState.GAME_OVER
        debug_print("TurnScheduler", "Game state set to GAME_OVER")
    

