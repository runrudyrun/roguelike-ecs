"""
World module for managing the game environment.
Handles map generation and entity creation.
"""
import random
from typing import List, Tuple, Set, Dict, Optional

from ecs.entity_manager import EntityManager
from components.position import Position
from components.renderable import Renderable
from components.health import Health
from components.combat_stats import CombatStats
from components.player_tag import PlayerTag
from components.ai_intent import AIIntent
from components.turn_state import TurnState

class World:
    """
    Manages the game world, including map generation and entity creation.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the game world
        
        Args:
            width: Width of the world map in tiles
            height: Height of the world map in tiles
        """
        self.width = width
        self.height = height
        
        # Wall positions
        self.walls: Set[Tuple[int, int]] = set()
        
        # Entity manager for this world
        self.entity_manager = EntityManager()
        
        # Keep track of the player entity ID
        self.player_id: Optional[int] = None
    
    def generate_map(self) -> None:
        """
        Generate a simple dungeon map
        
        For simplicity, just creates a bordered room with some random walls
        """
        # Clear any existing walls
        self.walls.clear()
        
        # Create borders
        for x in range(self.width):
            self.walls.add((x, 0))
            self.walls.add((x, self.height - 1))
            
        for y in range(self.height):
            self.walls.add((0, y))
            self.walls.add((self.width - 1, y))
        
        # Add some random walls (simple obstacles)
        num_walls = (self.width * self.height) // 20  # ~5% of the map
        
        for _ in range(num_walls):
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            self.walls.add((x, y))
    
    def is_wall(self, x: int, y: int) -> bool:
        """
        Check if a position is a wall
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position contains a wall, False otherwise
        """
        return (x, y) in self.walls
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """
        Check if a position is valid (in bounds and not a wall)
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the position is valid, False otherwise
        """
        return (0 <= x < self.width and 
                0 <= y < self.height and 
                not self.is_wall(x, y))
    
    def get_random_floor_position(self) -> Tuple[int, int]:
        """
        Get a random valid floor position (not a wall)
        
        Returns:
            (x, y) coordinates of a random floor tile
        """
        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            
            if not self.is_wall(x, y):
                return (x, y)
    
    def create_player(self) -> int:
        """
        Create the player entity
        
        Returns:
            Entity ID of the player
        """
        player_id = self.entity_manager.create_entity()
        
        # Get a valid starting position
        pos_x, pos_y = self.get_random_floor_position()
        
        # Add components to the player
        self.entity_manager.add_component(player_id, Position(pos_x, pos_y))
        self.entity_manager.add_component(player_id, Renderable('@', (255, 255, 255)))
        self.entity_manager.add_component(player_id, Health(30, 30))
        self.entity_manager.add_component(player_id, CombatStats(5, 2, 5))
        self.entity_manager.add_component(player_id, PlayerTag())
        self.entity_manager.add_component(player_id, TurnState(True))  # Player can act on first turn
        
        # Store the player ID
        self.player_id = player_id
        
        return player_id
    
    def create_enemy(self, enemy_type: str) -> int:
        """
        Create an enemy entity
        
        Args:
            enemy_type: Type of enemy to create ('goblin', 'orc', etc.)
            
        Returns:
            Entity ID of the enemy
        """
        enemy_id = self.entity_manager.create_entity()
        
        # Get a random position that's not too close to the player
        while True:
            pos_x, pos_y = self.get_random_floor_position()
            
            # Ensure the enemy is not too close to the player
            if self.player_id:
                player_pos = self.entity_manager.get_component(self.player_id, Position)
                distance = abs(player_pos.x - pos_x) + abs(player_pos.y - pos_y)
                
                if distance >= 5:  # Minimum distance from player
                    break
            else:
                break
        
        # Add base components
        self.entity_manager.add_component(enemy_id, Position(pos_x, pos_y))
        self.entity_manager.add_component(enemy_id, AIIntent())
        self.entity_manager.add_component(enemy_id, TurnState(True))  # Enemies can act on first turn
        
        # Configure enemy based on type
        if enemy_type == 'goblin':
            self.entity_manager.add_component(enemy_id, Renderable('g', (0, 255, 0)))
            self.entity_manager.add_component(enemy_id, Health(10, 10))
            self.entity_manager.add_component(enemy_id, CombatStats(3, 1, 3))
        elif enemy_type == 'orc':
            self.entity_manager.add_component(enemy_id, Renderable('o', (0, 200, 0)))
            self.entity_manager.add_component(enemy_id, Health(15, 15))
            self.entity_manager.add_component(enemy_id, CombatStats(4, 2, 4))
        elif enemy_type == 'troll':
            self.entity_manager.add_component(enemy_id, Renderable('T', (100, 100, 0)))
            self.entity_manager.add_component(enemy_id, Health(20, 20))
            self.entity_manager.add_component(enemy_id, CombatStats(5, 3, 6))
        else:
            # Default enemy
            self.entity_manager.add_component(enemy_id, Renderable('e', (255, 0, 0)))
            self.entity_manager.add_component(enemy_id, Health(8, 8))
            self.entity_manager.add_component(enemy_id, CombatStats(2, 0, 2))
        
        return enemy_id
    
    def populate_enemies(self, num_enemies: int) -> None:
        """
        Populate the world with a number of enemies
        
        Args:
            num_enemies: Number of enemies to create
        """
        enemy_types = ['goblin', 'orc', 'troll']
        
        for _ in range(num_enemies):
            enemy_type = random.choice(enemy_types)
            self.create_enemy(enemy_type)
