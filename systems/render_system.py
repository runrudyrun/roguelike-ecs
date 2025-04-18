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
from components.player_tag import PlayerTag
from components.health import Health
from components.combat_stats import CombatStats
from utils.debug import debug_print
from utils.message_queue import get_messages


class RenderSystem(System):
    """System responsible for rendering entities to the screen"""
    
    def __init__(self, screen_width: int, screen_height: int, 
                 tile_size: int, font_name: str = "courier", fullscreen: bool = False):
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
        
        # Store dimensions for toggling fullscreen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_fullscreen = fullscreen
        
        # Set display mode (fullscreen or windowed)
        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((screen_width, screen_height), flags)
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
        
        # Draw directly rendered UI elements
        self._render_direct_ui(entity_manager)
        
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
            
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """
        Wrap text to fit within a given width
        
        Args:
            text: Text to wrap
            font: Font to use for measuring text
            max_width: Maximum width in pixels
            
        Returns:
            List of wrapped text lines
        """
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = font.render(word + ' ', True, (0, 0, 0))  # Color doesn't matter for measuring
            word_width = word_surface.get_width()
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:  # Don't add empty lines
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
            
        # If no lines were created (e.g. single very long word), just return the original text
        return lines if lines else [text]
    
    def _render_direct_ui(self, entity_manager: EntityManager) -> None:
        """
        Directly render UI elements without using the UI system
        This ensures they're visible regardless of ECS integration issues
        
        Args:
            entity_manager: The entity manager
        """
        # Get player data
        player_entities = entity_manager.get_entities_with_components([PlayerTag])
        if not player_entities:
            debug_print("RenderSystem", "No player found for UI rendering")
            return
            
        player_id = next(iter(player_entities))
        health = entity_manager.get_component(player_id, Health)
        combat_stats = entity_manager.get_component(player_id, CombatStats)
        position = entity_manager.get_component(player_id, Position)
        
        if not health or not combat_stats or not position:
            debug_print("RenderSystem", "Missing player components for UI rendering")
            return
        
        # Calculate UI positions - top right of screen
        ui_width = 200  # pixels
        
        # Create a player info UI box
        info_rect = pygame.Rect(self.screen_width - ui_width, 0, ui_width, 120)
        pygame.draw.rect(self.screen, (0, 0, 0), info_rect)  # Black background
        pygame.draw.rect(self.screen, (200, 200, 200), info_rect, 2)  # White border
        
        # Draw player info title
        font = pygame.font.SysFont("courier", 14)
        title_surface = font.render("Player Info", True, (255, 255, 255))
        self.screen.blit(title_surface, (self.screen_width - ui_width + 10, 5))
        
        # Draw player stats
        stats_font = pygame.font.SysFont("courier", 12)
        stats = [
            f"HP: {health.current}/{health.max}",
            f"ATK: {combat_stats.attack}",
            f"DEF: {combat_stats.defense}",
            f"POS: ({position.x}, {position.y})"  
        ]
        
        for i, stat in enumerate(stats):
            stat_surf = stats_font.render(stat, True, (255, 255, 255))
            self.screen.blit(stat_surf, (self.screen_width - ui_width + 10, 30 + i * 20))
        
        # Create message log box below player info
        log_rect = pygame.Rect(self.screen_width - ui_width, 130, ui_width, 200)
        pygame.draw.rect(self.screen, (0, 0, 0), log_rect)  # Black background
        pygame.draw.rect(self.screen, (200, 200, 200), log_rect, 2)  # White border
        
        # Draw log title
        log_title = font.render("Message Log", True, (255, 255, 255))
        self.screen.blit(log_title, (self.screen_width - ui_width + 10, 135))
        
        # Get recent messages from message queue
        messages = get_messages(8)  # Show up to 8 messages
        if not messages:
            # If no messages, show a default message
            empty_text = stats_font.render("(No messages)", True, (150, 150, 150))
            self.screen.blit(empty_text, (self.screen_width - ui_width + 10, 160))
        else:
            # Display messages in the log (most recent at the bottom)
            y_offset = 160
            for text, color in messages:
                # Wrap text if needed
                wrapped_text = self._wrap_text(text, stats_font, ui_width - 20)
                for line in wrapped_text:
                    msg_surf = stats_font.render(line, True, color)
                    self.screen.blit(msg_surf, (self.screen_width - ui_width + 10, y_offset))
                    y_offset += 16  # Line spacing
    
    def toggle_fullscreen(self) -> None:
        """
        Toggle between fullscreen and windowed mode
        """
        self.is_fullscreen = not self.is_fullscreen
        flags = pygame.FULLSCREEN if self.is_fullscreen else 0
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
        # Force UI elements to recalculate their positions
        pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, 
                                            {'w': self.screen_width, 'h': self.screen_height}))
