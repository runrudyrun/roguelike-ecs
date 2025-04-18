"""
Render System module for the ECS architecture.
Responsible for rendering all entities with renderable components.
"""
import pygame
from typing import Dict, Tuple, List, Optional

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.position import Position
from components.renderable import Renderable


class RenderSystem(System):
    """System responsible for rendering entities to the screen"""
    
    def __init__(self, screen_width: int, screen_height: int, 
                 tile_size: int, font_name: str = "courier"):
        """
        Initialize the render system
        
        Args:
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels
            tile_size: Size of each tile in pixels
            font_name: Name of the font to use
        """
        super().__init__()
        
        # Required components for this system
        self._required_component_types = [Position, Renderable]
        
        # Set a high priority so rendering happens last
        self._priority = 100
        
        # Initialize pygame and set up the screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        
        # Calculate the grid dimensions
        self.grid_width = screen_width // tile_size
        self.grid_height = screen_height // tile_size
        
        # Initialize pygame components
        pygame.font.init()
        self.font = pygame.font.SysFont(font_name, tile_size)
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Roguelike ECS")
        
        # Camera offset (for scrolling)
        self.camera_x = 0
        self.camera_y = 0
        
        # Render cache to avoid recreating surfaces every frame
        self._render_cache: Dict[str, pygame.Surface] = {}
        
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Render all entities with Position and Renderable components
        
        Args:
            entity_manager: The entity manager containing all entities and components
            dt: Delta time since last update (not used for rendering)
        """
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Get all entities with position and renderable components
        render_entities = entity_manager.get_entities_with_components(
            [Position, Renderable]
        )
        
        # Sort entities by render priority
        sorted_entities = sorted(
            render_entities,
            key=lambda eid: entity_manager.get_component(eid, Renderable).render_priority
        )
        
        # Render each entity
        for entity_id in sorted_entities:
            position = entity_manager.get_component(entity_id, Position)
            renderable = entity_manager.get_component(entity_id, Renderable)
            
            # Skip if not visible
            if not renderable.visible:
                continue
                
            # Calculate screen position (apply camera offset)
            screen_x = (position.x - self.camera_x) * self.tile_size
            screen_y = (position.y - self.camera_y) * self.tile_size
            
            # Skip if outside the visible area
            if (screen_x < -self.tile_size or screen_x > self.screen_width or
                screen_y < -self.tile_size or screen_y > self.screen_height):
                continue
            
            # Render the entity
            self._render_entity(screen_x, screen_y, renderable)
        
        # Update the display
        pygame.display.flip()
    
    def _render_entity(self, x: int, y: int, renderable: Renderable) -> None:
        """
        Render a single entity at the given screen position
        
        Args:
            x: X coordinate on screen (pixels)
            y: Y coordinate on screen (pixels)
            renderable: The renderable component
        """
        # Create a unique key for this renderable
        cache_key = f"{renderable.char}_{renderable.color}_{renderable.bg_color}"
        
        # Check if we have a cached surface
        if cache_key not in self._render_cache:
            # Create a new surface for this character
            char_surface = self.font.render(
                renderable.char, True, renderable.color, renderable.bg_color
            )
            self._render_cache[cache_key] = char_surface
        
        # Blit the cached surface to the screen
        self.screen.blit(self._render_cache[cache_key], (x, y))
    
    def center_camera_on_entity(self, entity_id: int, 
                               entity_manager: EntityManager) -> None:
        """
        Center the camera on a specific entity
        
        Args:
            entity_id: The ID of the entity to center on
            entity_manager: The entity manager
        """
        position = entity_manager.get_component(entity_id, Position)
        if position:
            self.camera_x = position.x - (self.grid_width // 2)
            self.camera_y = position.y - (self.grid_height // 2)
