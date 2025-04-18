"""
AI System module for the ECS architecture.
Responsible for enemy AI decision making.
"""
import random
from typing import Dict, List, Tuple, Optional, Set

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.position import Position
from components.ai_intent import AIIntent, ActionType
from components.health import Health
from components.combat_stats import CombatStats
from components.player_tag import PlayerTag
from utils.debug import debug_print

class AISystem(System):
    """System responsible for AI decision making"""
    
    def __init__(self, detection_range: int = 8):
        """
        Initialize the AI system
        
        Args:
            detection_range: How far AI entities can detect the player
        """
        super().__init__()
        
        # Required components for this system
        self._required_component_types = [AIIntent, Position]
        
        # Set a moderate-high priority so AI decisions are made before movement
        self._priority = -10
        
        # Detection range for AI entities
        self.detection_range = detection_range
        
        # Simple pathfinding cache
        self._path_cache: Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[Tuple[int, int]]] = {}
    
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Make decisions for all AI entities in the current turn
        In the new simplified turn-based system, this is called after player action
        to decide what all enemies will do in this turn
        
        Args:
            entity_manager: The entity manager
            dt: Delta time since last update
        """
        debug_print("AISystem", "Update called for all AI entities in this turn")
        
        # Get player entity
        player_entities = entity_manager.get_entities_with_components([PlayerTag, Position])
        if not player_entities:
            debug_print("AISystem", "No player entities found, skipping update")
            return  # No player to interact with
        
        player_id = next(iter(player_entities))
        player_pos = entity_manager.get_component(player_id, Position)
        
        # Get all AI entities
        ai_entities = entity_manager.get_entities_with_components(self._required_component_types)
        debug_print("AISystem", f"Found {len(ai_entities)} AI entities with required components")
        
        active_entities = 0
        # Process each AI entity
        for entity_id in ai_entities:
            # Skip if entity is dead
            health = entity_manager.get_component(entity_id, Health)
            if not health or not health.is_alive():
                debug_print("AISystem", f"Entity {entity_id} is dead, skipping")
                continue
                
            debug_print("AISystem", f"Processing AI for entity {entity_id}")
            active_entities += 1
                
            ai_intent = entity_manager.get_component(entity_id, AIIntent)
            position = entity_manager.get_component(entity_id, Position)
            
            # Calculate distance to player
            distance = self._manhattan_distance(
                (position.x, position.y), 
                (player_pos.x, player_pos.y)
            )
            debug_print("AISystem", f"Entity {entity_id} at ({position.x},{position.y}), distance to player: {distance}")
            
            # Make decisions based on distance and other factors
            if distance <= 1:
                debug_print("AISystem", f"Entity {entity_id} is adjacent to player, deciding to attack")
                # Adjacent to player - attack
                self._decide_attack(entity_manager, entity_id, player_id, ai_intent)
            elif distance <= self.detection_range:
                debug_print("AISystem", f"Entity {entity_id} is within detection range, deciding to chase")
                # Within detection range - chase player
                self._decide_chase(entity_manager, entity_id, player_id, position, player_pos, ai_intent)
            else:
                debug_print("AISystem", f"Entity {entity_id} is out of detection range, deciding to wander")
                # Outside detection range - wander randomly
                self._decide_wander(entity_manager, entity_id, position, ai_intent)
            
            # In our simplified turn-based system, we're no longer tracking turn state per entity
            # The GameLoop now manages the entire turn for all entities
            # Simply log the decision made
            debug_print("AISystem", f"Entity {entity_id} has made a decision: {ai_intent.action_type}")
        
        debug_print("AISystem", f"Processed {active_entities} active AI entities")
    
    def _decide_attack(self, entity_manager: EntityManager, 
                      entity_id: int, player_id: int, ai_intent: AIIntent) -> None:
        """
        Decide to attack the player
        
        Args:
            entity_manager: The entity manager
            entity_id: ID of the AI entity
            player_id: ID of the player entity
            ai_intent: AIIntent component of the AI entity
        """
        # Check if entity has combat stats
        if entity_manager.has_component(entity_id, CombatStats):
            # Set attack intent
            ai_intent.set_attack_intent(player_id)
    
    def _decide_chase(self, entity_manager: EntityManager, entity_id: int, 
                     player_id: int, position: Position, player_pos: Position,
                     ai_intent: AIIntent) -> None:
        """
        Decide to chase the player
        
        Args:
            entity_manager: The entity manager
            entity_id: ID of the AI entity
            player_id: ID of the player entity
            position: Position component of the AI entity
            player_pos: Position component of the player entity
            ai_intent: AIIntent component of the AI entity
        """
        # Simple A* pathfinding would go here
        # For now, just move towards the player using a simple algorithm
        
        # Try to find a path
        path = self._find_path(entity_manager, 
                              (position.x, position.y), 
                              (player_pos.x, player_pos.y))
        
        if path and len(path) > 1:
            # Move to the next position in the path
            next_pos = path[1]  # path[0] is current position
            ai_intent.set_move_intent(next_pos[0], next_pos[1])
        else:
            # Simple direct movement towards player if no path found
            dx = 0
            dy = 0
            
            if player_pos.x > position.x:
                dx = 1
            elif player_pos.x < position.x:
                dx = -1
                
            if player_pos.y > position.y:
                dy = 1
            elif player_pos.y < position.y:
                dy = -1
            
            target_x = position.x + dx
            target_y = position.y + dy
            
            ai_intent.set_move_intent(target_x, target_y)
    
    def _decide_wander(self, entity_manager: EntityManager, 
                      entity_id: int, position: Position, ai_intent: AIIntent) -> None:
        """
        Decide to wander randomly
        
        Args:
            entity_manager: The entity manager
            entity_id: ID of the AI entity
            position: Position component of the AI entity
            ai_intent: AIIntent component of the AI entity
        """
        # 30% chance to move in a random direction
        if random.random() < 0.3:
            # Pick a random direction
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            
            # Avoid diagonal movement for simplicity
            if dx != 0 and dy != 0:
                if random.random() < 0.5:
                    dx = 0
                else:
                    dy = 0
            
            target_x = position.x + dx
            target_y = position.y + dy
            
            ai_intent.set_move_intent(target_x, target_y)
        else:
            # Wait
            ai_intent.set_wait_intent()
    
    def _manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """
        Calculate Manhattan distance between two positions
        
        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)
            
        Returns:
            Manhattan distance between the positions
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _find_path(self, entity_manager: EntityManager, 
                  start: Tuple[int, int], goal: Tuple[int, int], 
                  max_steps: int = 20) -> List[Tuple[int, int]]:
        """
        Find a path from start to goal using A* algorithm
        
        Args:
            entity_manager: The entity manager
            start: Starting position (x, y)
            goal: Goal position (x, y)
            max_steps: Maximum number of steps in the path
            
        Returns:
            List of positions from start to goal, or empty list if no path found
        """
        # Check path cache
        cache_key = (start, goal)
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]
        
        # Simple implementation for now - would be expanded in a full game
        # This is a simplified version that just returns direct path
        # A real implementation would use A* and account for obstacles
        
        path = [start]
        current = start
        
        # Generate a simple path (not accounting for obstacles)
        for _ in range(max_steps):
            if current == goal:
                break
                
            # Move in the direction that reduces distance to goal
            x, y = current
            
            # Determine best direction
            if x < goal[0]:
                next_x = x + 1
            elif x > goal[0]:
                next_x = x - 1
            else:
                next_x = x
                
            if y < goal[1]:
                next_y = y + 1
            elif y > goal[1]:
                next_y = y - 1
            else:
                next_y = y
            
            # Avoid moving diagonally for simplicity
            if next_x != x and next_y != y:
                # Prefer horizontal movement first
                if random.random() < 0.5:
                    next_y = y
                else:
                    next_x = x
            
            current = (next_x, next_y)
            path.append(current)
            
            if current == goal:
                break
        
        # Cache the path for future use
        self._path_cache[cache_key] = path
        
        return path
