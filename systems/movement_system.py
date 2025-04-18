"""
Movement System module for the ECS architecture.
Handles entity movement and collision detection.
"""
from typing import Dict, Set, Tuple, Optional, List

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.position import Position
from components.ai_intent import AIIntent, ActionType
from components.player_tag import PlayerTag
from utils.debug import debug_print
from utils.message_queue import add_message

class MovementSystem(System):
    """System responsible for entity movement and collision detection"""
    
    def __init__(self):
        """Initialize the movement system"""
        super().__init__()
        
        # Required components for this system
        self._required_component_types = [Position]
        
        # Set a moderate priority
        self._priority = 0
        
        # Occupancy map: position tuple -> entity_id
        self._occupancy_map: Dict[Tuple[int, int], int] = {}
        
        # Movement directions (dx, dy)
        self.directions = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
            "wait": (0, 0)
        }
        
        # List of impassable positions (walls, etc.)
        self._impassable_positions: Set[Tuple[int, int]] = set()
    
    def try_move_entity(self, entity_manager: EntityManager, entity_id: int, 
                         dx: int, dy: int) -> bool:
        """
        Try to move an entity in the specified direction
        
        Args:
            entity_manager: The entity manager
            entity_id: ID of the entity to move
            dx: Change in x position
            dy: Change in y position
            
        Returns:
            True if the move was successful, False otherwise
        """
        # Get the entity's position
        position = entity_manager.get_component(entity_id, Position)
        if not position:
            return False
        
        # Calculate the new position
        new_x = position.x + dx
        new_y = position.y + dy
        
        # Check if the move is valid
        if not self._is_valid_move(entity_manager, entity_id, new_x, new_y):
            # Log collision message for player
            is_player = entity_manager.has_component(entity_id, PlayerTag)
            if is_player:
                # Check what's blocking the way
                if (new_x, new_y) in self._impassable_positions:
                    add_message("You bump into a wall.", (200, 200, 200))
                else:
                    # Check if there's an entity there
                    blocking_entity = self._occupancy_map.get((new_x, new_y))
                    if blocking_entity:
                        add_message("There's something in the way.", (200, 200, 200))
            return False
        
        # Update the occupancy map
        old_pos = (position.x, position.y)
        new_pos = (new_x, new_y)
        
        if old_pos in self._occupancy_map and self._occupancy_map[old_pos] == entity_id:
            del self._occupancy_map[old_pos]
        
        self._occupancy_map[new_pos] = entity_id
        
        # Move the entity
        position.set_position(new_x, new_y)
        
        # Log movement for player
        is_player = entity_manager.has_component(entity_id, PlayerTag)
        if is_player and (dx != 0 or dy != 0):
            direction = self._get_direction_name(dx, dy)
            add_message(f"You move {direction}.", (180, 180, 220))
            
        return True
    
    def _is_valid_move(self, entity_manager: EntityManager, entity_id: int, 
                       x: int, y: int) -> bool:
        """
        Check if a move to the specified position is valid
        
        Args:
            entity_manager: The entity manager
            entity_id: ID of the entity trying to move
            x: Target x position
            y: Target y position
            
        Returns:
            True if the move is valid, False otherwise
        """
        # Check for map boundaries or other environmental constraints
        if (x, y) in self._impassable_positions:
            return False
        
        # Check if position is occupied by another entity
        if (x, y) in self._occupancy_map and self._occupancy_map[(x, y)] != entity_id:
            # This position is occupied by another entity
            return False
        
        return True
    
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Process movement for all entities with movement intents
        In the simplified turn-based system, this is called once per turn after
        input and AI decisions are made
        
        Args:
            entity_manager: The entity manager
            dt: Delta time since last update
        """
        debug_print("MovementSystem", "Update called for all entities with movement intents")
        
        # Rebuild the occupancy map first
        self._rebuild_occupancy_map(entity_manager)
        
        # Process AI movement intents - get entities with Position, AIIntent
        ai_entities = entity_manager.get_entities_with_components([Position, AIIntent])
        debug_print("MovementSystem", f"Found {len(ai_entities)} entities with Position and AIIntent")
        
        moved_entities = 0
        
        for entity_id in ai_entities:
            ai_intent = entity_manager.get_component(entity_id, AIIntent)
            debug_print("MovementSystem", f"Entity {entity_id} has action_type={ai_intent.action_type}, target_position={ai_intent.target_position}")
            
            # Only process entities with movement intent
            if ai_intent.action_type == ActionType.MOVE and ai_intent.target_position:
                # Get current position
                position = entity_manager.get_component(entity_id, Position)
                target_x, target_y = ai_intent.target_position
                debug_print("MovementSystem", f"Entity {entity_id} wants to move to ({target_x},{target_y}) from ({position.x},{position.y})")
                
                # Calculate direction
                dx = 0
                dy = 0
                
                if target_x > position.x:
                    dx = 1
                elif target_x < position.x:
                    dx = -1
                    
                if target_y > position.y:
                    dy = 1
                elif target_y < position.y:
                    dy = -1
                
                debug_print("MovementSystem", f"Entity {entity_id} moving with dx={dx}, dy={dy}")
                
                # Try to move towards the target position
                move_result = self.try_move_entity(entity_manager, entity_id, dx, dy)
                debug_print("MovementSystem", f"Entity {entity_id} move result: {move_result}")
                
                if move_result:
                    moved_entities += 1
                
                # Clear the intent after processing
                ai_intent.clear_intent()
                debug_print("MovementSystem", f"Cleared intent for Entity {entity_id}")
        
        debug_print("MovementSystem", f"Moved {moved_entities} entities this update")
    
    def _rebuild_occupancy_map(self, entity_manager: EntityManager) -> None:
        """
        Rebuild the occupancy map from entity positions
        
        Args:
            entity_manager: The entity manager
        """
        self._occupancy_map.clear()
        
        # Get all entities with a position
        position_entities = entity_manager.get_entities_with_components([Position])
        
        # Build the occupancy map
        for entity_id in position_entities:
            position = entity_manager.get_component(entity_id, Position)
            self._occupancy_map[(position.x, position.y)] = entity_id
    
    def set_impassable_positions(self, positions: List[Tuple[int, int]]) -> None:
        """
        Set positions that cannot be moved into (walls, etc.)
        
        Args:
            positions: List of (x, y) tuples representing impassable positions
        """
        self._impassable_positions = set(positions)
    
    def get_entity_at_position(self, x: int, y: int) -> Optional[int]:
        """
        Get the entity ID at a specific position
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Entity ID at the position, or None if no entity is there
        """
        return self._occupancy_map.get((x, y))
    
    def _get_direction_name(self, dx: int, dy: int) -> str:
        """
        Get a human-readable direction name from delta coordinates
        
        Args:
            dx: Change in x position
            dy: Change in y position
            
        Returns:
            Direction name as string
        """
        if dx == 0 and dy == -1:
            return "north"
        elif dx == 0 and dy == 1:
            return "south"
        elif dx == -1 and dy == 0:
            return "west"
        elif dx == 1 and dy == 0:
            return "east"
        elif dx == 1 and dy == -1:
            return "northeast"
        elif dx == 1 and dy == 1:
            return "southeast"
        elif dx == -1 and dy == -1:
            return "northwest"
        elif dx == -1 and dy == 1:
            return "southwest"
        else:
            return "nowhere"
