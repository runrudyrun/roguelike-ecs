"""
UI System module for the ECS architecture.
Responsible for rendering UI components.
"""
import pygame
from typing import Dict, List, Tuple, Optional, Any, Set
import time

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.ui_component import (
    UIComponent, 
    UIWindowComponent, 
    UIPlayerInfoComponent, 
    UILogComponent
)
from components.health import Health
from components.combat_stats import CombatStats
from components.position import Position
from components.player_tag import PlayerTag
from utils.debug import debug_print
from systems.turn_scheduler_system import TurnSchedulerSystem


class UISystem(System):
    """System responsible for rendering UI components"""
    
    def __init__(self, screen: pygame.Surface, tile_size: int, 
                font_name: str = "courier", font_size: Optional[int] = None):
        """
        Initialize the UI system
        
        Args:
            screen: Pygame surface to render to
            tile_size: Size of a tile in pixels
            font_name: Name of the font to use
            font_size: Font size (defaults to tile_size-2 if None)
        """
        super().__init__()
        
        # Set a very high priority to ensure UI renders after everything else
        self._priority = 200
        
        # Reference to the screen
        self.screen = screen
        self.tile_size = tile_size
        self.font_size = font_size if font_size is not None else tile_size - 2
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont(font_name, self.font_size)
        
        # Cache for rendered text
        self._text_cache: Dict[str, pygame.Surface] = {}
        
        # Setup the UI components entities
        # These will be added to the entity manager in initialize()
        self.player_info_entity_id: Optional[int] = None
        self.log_entity_id: Optional[int] = None
        
        # For performance monitoring
        self._last_update_time = time.time()
        
        debug_print("UISystem", "UI System initialized")
    
    def initialize(self, entity_manager: EntityManager) -> None:
        """
        Initialize UI components and entities
        
        Args:
            entity_manager: The entity manager
        """
        debug_print("UISystem", "Creating UI entities")
        
        # Calculate positions in grid coordinates - place UI in the top-right area
        screen_width_grid = self.screen.get_width() // self.tile_size
        player_info_width = min(25, screen_width_grid // 3)  # Limit to 25 grid units or 1/3 of screen
        player_info_x = screen_width_grid - player_info_width
        
        # Create player info UI in the top right
        player_info_id = entity_manager.create_entity()
        entity_manager.add_component(
            player_info_id, 
            UIPlayerInfoComponent(player_info_x, 0, player_info_width, 6)
        )
        self.player_info_entity_id = player_info_id
        
        # Create message log UI below the player info
        log_id = entity_manager.create_entity()
        entity_manager.add_component(
            log_id, 
            UILogComponent(player_info_x, 7, player_info_width, 12)
        )
        self.log_entity_id = log_id
        
        # Add welcome messages
        log_component = entity_manager.get_component(log_id, UILogComponent)
        if log_component:
            log_component.add_message("Welcome to Roguelike ECS!", (150, 255, 150))
            log_component.add_message("Use arrow keys to move", (200, 200, 200))
            log_component.add_message("Press 'a' to attack enemies", (200, 200, 200))
            log_component.add_message("Press 'q' to quit", (200, 200, 200))
        
        debug_print("UISystem", f"Created UI entities: PlayerInfo={player_info_id}, Log={log_id}")
    
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Update and render all UI components
        
        Args:
            entity_manager: The entity manager
            dt: Delta time since last update
        """
        # First check if our UI entities exist
        if not self.player_info_entity_id or not self.log_entity_id:
            debug_print("UISystem", "UI entities not initialized, reinitializing")
            self.initialize(entity_manager)
            return
            
        # Update player info if needed (only every 0.2 seconds)
        current_time = time.time()
        if current_time - self._last_update_time > 0.2:
            self._update_player_info(entity_manager)
            self._last_update_time = current_time
        
        # Get all entities with UI components
        ui_entities = entity_manager.get_entities_with_components([UIComponent])
        debug_print("UISystem", f"Found {len(ui_entities)} UI entities to render")
        
        # Sort by z-index to ensure proper layering
        sorted_ui_entities = sorted(
            ui_entities,
            key=lambda eid: entity_manager.get_component(eid, UIComponent).z_index
        )
        
        # Render each UI component
        for entity_id in sorted_ui_entities:
            ui_component = entity_manager.get_component(entity_id, UIComponent)
            
            # Skip if not visible
            if not ui_component.visible:
                continue
            
            # Render the component based on its type
            if isinstance(ui_component, UIPlayerInfoComponent):
                self._render_player_info(ui_component)
            elif isinstance(ui_component, UILogComponent):
                self._render_log(ui_component)
            elif isinstance(ui_component, UIWindowComponent):
                self._render_window(ui_component)
            else:
                self._render_ui_component(ui_component)
    
    def _update_player_info(self, entity_manager: EntityManager) -> None:
        """
        Update player info with current data
        
        Args:
            entity_manager: The entity manager
        """
        if not self.player_info_entity_id:
            return
            
        player_info = entity_manager.get_component(
            self.player_info_entity_id, UIPlayerInfoComponent
        )
        if not player_info:
            return
        
        # Find player entity
        player_entities = entity_manager.get_entities_with_components([PlayerTag])
        if not player_entities:
            return
        
        player_id = next(iter(player_entities))
        
        # Get player components
        health = entity_manager.get_component(player_id, Health)
        combat_stats = entity_manager.get_component(player_id, CombatStats)
        position = entity_manager.get_component(player_id, Position)
        
        # Update player info component with current data
        if health:
            player_info.health_current = health.current
            player_info.health_max = health.max
        
        if combat_stats:
            player_info.attack = combat_stats.attack
            player_info.defense = combat_stats.defense
        
        if position:
            player_info.position_x = position.x
            player_info.position_y = position.y
        
        # Get turn count from systems
        from systems.turn_scheduler_system import TurnSchedulerSystem
        component_store = entity_manager.get_component_store()
        turn_scheduler = component_store.get_system("TurnSchedulerSystem")
        if turn_scheduler:
            player_info.turn_count = turn_scheduler.turn_number
        else:
            debug_print("UISystem", "Could not find TurnSchedulerSystem for turn count")
    
    def _render_ui_component(self, component: UIComponent) -> None:
        """
        Render a generic UI component
        
        Args:
            component: UI component to render
        """
        # Convert grid coordinates to pixel coordinates
        x = component.x * self.tile_size
        y = component.y * self.tile_size
        width = component.width * self.tile_size
        height = component.height * self.tile_size
        
        # Draw background
        pygame.draw.rect(
            self.screen, 
            component.bg_color, 
            (x, y, width, height)
        )
        
        # Draw border if needed
        if component.has_border:
            pygame.draw.rect(
                self.screen, 
                component.border_color, 
                (x, y, width, height), 
                1
            )
    
    def _render_window(self, window: UIWindowComponent) -> None:
        """
        Render a window UI component
        
        Args:
            window: Window UI component to render
        """
        # First render the base component (background and border)
        self._render_ui_component(window)
        
        # Convert grid coordinates to pixel coordinates
        x = window.x * self.tile_size
        y = window.y * self.tile_size
        
        # Render title if it exists
        if window.title:
            title_surface = self._get_text_surface(
                window.title, window.title_color
            )
            # Center the title
            title_x = x + (window.width * self.tile_size - title_surface.get_width()) // 2
            self.screen.blit(title_surface, (title_x, y + 2))
            
            # Draw line under title
            line_y = y + self.font_size + 4
            pygame.draw.line(
                self.screen,
                window.border_color,
                (x + 2, line_y),
                (x + window.width * self.tile_size - 2, line_y)
            )
    
    def _render_player_info(self, info: UIPlayerInfoComponent) -> None:
        """
        Render the player info UI component
        
        Args:
            info: Player info UI component to render
        """
        # First render as a window
        self._render_window(info)
        
        # Convert grid coordinates to pixel coordinates
        x = info.x * self.tile_size
        y = info.y * self.tile_size
        
        # Padding from window edge and title
        padding_x = 5
        padding_y = self.font_size + 8  # Account for title height
        
        # Render stats
        stats = [
            f"HP: {info.health_current}/{info.health_max}",
            f"ATK: {info.attack}",
            f"DEF: {info.defense}",
            f"Pos: ({info.position_x}, {info.position_y})",
            f"Turn: {info.turn_count}"
        ]
        
        for i, stat in enumerate(stats):
            stat_surface = self._get_text_surface(stat, (255, 255, 255))
            self.screen.blit(
                stat_surface, 
                (x + padding_x, y + padding_y + i * (self.font_size + 2))
            )
    
    def _render_log(self, log: UILogComponent) -> None:
        """
        Render the message log UI component
        
        Args:
            log: Log UI component to render
        """
        # First render as a window
        self._render_window(log)
        
        # Convert grid coordinates to pixel coordinates
        x = log.x * self.tile_size
        y = log.y * self.tile_size
        
        # Padding from window edge and title
        padding_x = 5
        padding_y = self.font_size + 8  # Account for title height
        
        # Get the last N messages that fit in the window
        max_visible_lines = (log.height * self.tile_size - padding_y) // (self.font_size + 2)
        visible_messages = log.messages[-max_visible_lines:]
        
        # Render messages
        for i, (message, color) in enumerate(visible_messages):
            msg_surface = self._get_text_surface(message, color)
            self.screen.blit(
                msg_surface, 
                (x + padding_x, y + padding_y + i * (self.font_size + 2))
            )
    
    def _get_text_surface(self, text: str, color: Tuple[int, int, int]) -> pygame.Surface:
        """
        Get a cached text surface for the given text and color
        
        Args:
            text: Text to render
            color: Color of the text (RGB tuple)
            
        Returns:
            Rendered text surface
        """
        cache_key = f"{text}_{color[0]}_{color[1]}_{color[2]}"
        
        if cache_key not in self._text_cache:
            self._text_cache[cache_key] = self.font.render(text, True, color)
            
            # Limit cache size to avoid memory issues
            if len(self._text_cache) > 1000:
                # Remove a random item (simple approach)
                self._text_cache.pop(next(iter(self._text_cache)))
        
        return self._text_cache[cache_key]
    
    def log_message(self, entity_manager: EntityManager, message: str, 
                    color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """
        Add a message to the message log
        
        Args:
            entity_manager: The entity manager
            message: Message to add
            color: Color of the message (RGB tuple)
        """
        if not self.log_entity_id:
            debug_print("UISystem", f"Cannot log message, no log entity: {message}")
            return
        
        log_component = entity_manager.get_component(
            self.log_entity_id, UILogComponent
        )
        if log_component:
            log_component.add_message(message, color)
            debug_print("UISystem", f"Added message to log: {message}")
