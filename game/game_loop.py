"""
Game Loop module for the ECS architecture.
Manages the main game loop and system execution.
"""
import pygame
import sys
from typing import List, Dict, Optional, Tuple

from ecs.system import System, SystemRegistry
from ecs.entity_manager import EntityManager
from systems.input_system import InputSystem
from systems.render_system import RenderSystem
from systems.movement_system import MovementSystem
from systems.combat_system import CombatSystem
from systems.ai_system import AISystem
from systems.turn_scheduler_system import TurnSchedulerSystem, GameState
from systems.ui_system import UISystem
from utils.debug import debug_print
from utils.message_queue import add_message
from game.world import World
from components.position import Position

class GameLoop:
    """
    Manages the main game loop and system execution.
    """
    
    def __init__(self, screen_width: int, screen_height: int, tile_size: int, fullscreen: bool = False):
        """
        Initialize the game loop
        
        Args:
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels
            tile_size: Size of each tile in pixels
        """
        # Initialize pygame
        pygame.init()
        
        # Store fullscreen flag
        self.fullscreen = fullscreen
        
        # Calculate world dimensions based on screen size
        world_width = screen_width // tile_size
        world_height = screen_height // tile_size
        
        # Create the world
        self.world = World(world_width, world_height)
        
        # Get a reference to the entity manager
        self.entity_manager = self.world.entity_manager
        
        # Create the system registry
        self.systems = SystemRegistry()
        # Register the entity manager with the system registry
        self.systems.set_entity_manager(self.entity_manager)
        
        # Generate the world and create the player first
        # This ensures player exists before systems try to use it
        self.world.generate_map()
        self.world.create_player()
        self.world.populate_enemies(10)
        
        # Create all the systems
        self.systems = SystemRegistry()
        
        # Input system
        self.input_system = InputSystem()
        self.systems.add_system(self.input_system)
        
        # Turn scheduler system (depends on input system)
        self.turn_scheduler = TurnSchedulerSystem(self.input_system)
        self.systems.add_system(self.turn_scheduler)
        
        # AI system
        self.ai_system = AISystem()
        self.systems.add_system(self.ai_system)
        
        # Movement system
        self.movement_system = MovementSystem()
        self.systems.add_system(self.movement_system)
        
        # Combat system
        self.combat_system = CombatSystem()
        self.systems.add_system(self.combat_system)
        
        # Render system
        self.render_system = RenderSystem(screen_width, screen_height, tile_size, fullscreen=self.fullscreen)
        self.systems.add_system(self.render_system)
        
        # UI system (must be added last to render on top)
        self.ui_system = UISystem(self.render_system.screen, tile_size)
        self.systems.add_system(self.ui_system)
        
        # Register input action callbacks
        self._register_input_callbacks()
        
        # Initialize the systems
        self.systems.initialize()
        
        # Initialize UI system
        self.ui_system.initialize(self.entity_manager)
        
        # Add some message log listeners to game events
        self._register_event_listeners()
        
        # Send initial welcome messages to the log
        debug_print("GameLoop", "Sending initial welcome messages")
        add_message("Welcome to Roguelike ECS!", (150, 255, 150))
        add_message("Use arrow keys to move", (200, 200, 255))
        add_message("Press 'a' to attack enemies", (200, 200, 255))
        add_message("Press 'F11' to toggle fullscreen", (200, 200, 255))
        add_message("Press 'q' to quit", (200, 200, 255))
        
        # Game clock for timing
        self.clock = pygame.time.Clock()
        
        # Flag for running the game loop
        self.running = True
    
    def _register_input_callbacks(self) -> None:
        """Register callbacks for input actions"""
        from systems.input_system import InputAction
        
        # Movement actions
        self.input_system.register_action_callback(
            InputAction.MOVE_UP,
            lambda em, player_id: self.movement_system.try_move_entity(em, player_id, 0, -1)
        )
        self.input_system.register_action_callback(
            InputAction.MOVE_DOWN,
            lambda em, player_id: self.movement_system.try_move_entity(em, player_id, 0, 1)
        )
        self.input_system.register_action_callback(
            InputAction.MOVE_LEFT,
            lambda em, player_id: self.movement_system.try_move_entity(em, player_id, -1, 0)
        )
        self.input_system.register_action_callback(
            InputAction.MOVE_RIGHT,
            lambda em, player_id: self.movement_system.try_move_entity(em, player_id, 1, 0)
        )
        
        # Wait action
        self.input_system.register_action_callback(
            InputAction.WAIT,
            lambda em, player_id: True  # Just advance the turn
        )
        
        # Attack action (handled differently, needs target selection)
        self.input_system.register_action_callback(
            InputAction.ATTACK,
            self._handle_attack_action
        )
        
        # Toggle fullscreen action
        self.input_system.register_action_callback(
            InputAction.TOGGLE_FULLSCREEN,
            lambda em, player_id: self._toggle_fullscreen()
        )
    
    def _handle_attack_action(self, entity_manager: EntityManager, player_id: int) -> bool:
        """
        Handle player attack action
        
        Args:
            entity_manager: The entity manager
            player_id: ID of the player entity
            
        Returns:
            True if an attack was performed, False otherwise
        """
        # Get player position
        player_pos = entity_manager.get_component(player_id, Position)
        if not player_pos:
            return False
        
        # Check adjacent tiles for enemies
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        for dx, dy in directions:
            target_x = player_pos.x + dx
            target_y = player_pos.y + dy
            
            # Get entity at this position
            target_id = self.movement_system.get_entity_at_position(target_x, target_y)
            
            # If there's an entity and it's not the player
            if target_id and target_id != player_id:
                # Check if we can attack it
                if self.combat_system.can_attack(entity_manager, player_id, target_id):
                    # Perform the attack
                    self.combat_system.perform_attack(entity_manager, player_id, target_id)
                    return True
        
        return False
    
    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode"""
        self.render_system.toggle_fullscreen()
        # Return True so the input system knows we performed an action
        return True
    
    def initialize_game(self) -> None:
        """Initialize the game state and configure systems"""
        # Pass wall positions to the movement system
        self.movement_system.set_impassable_positions(list(self.world.walls))
        
        # Center the camera on the player
        if self.world.player_id:
            self.render_system.center_camera_on_entity(self.world.player_id, self.entity_manager)
        
        # Game startup messages are now handled in __init__
    
    def update(self, dt: float) -> None:
        """
        Process a single game turn with player action followed by enemy actions
        
        Args:
            dt: Delta time in seconds since last update
        """
        # Process player's action first
        self.input_system.update(self.entity_manager, dt)
        
        # If player took action, process the consequences and then enemy turns
        if self.input_system.action_taken:
            # Reset action taken flag for next turn
            self.input_system.action_taken = False
            
            # Log turn start (only every 5 turns to avoid spam)
            turn_num = self.turn_scheduler.turn_number + 1
            if turn_num % 5 == 0:
                add_message(f"Turn {turn_num}", (180, 180, 180))
            
            # Process AI decisions for all enemies
            self.ai_system.update(self.entity_manager, dt)
            
            # Process movement for all entities that have intents
            self.movement_system.update(self.entity_manager, dt)
            
            # Process combat
            self.combat_system.update(self.entity_manager, dt)
            
            # Clean up any entities marked for deletion
            self.entity_manager.cleanup_entities()
            
            # Increment turn counter in the turn scheduler
            self.turn_scheduler.advance_turn()
        
        # Render the current game state regardless of turn progression
        self.render_system.update(self.entity_manager, dt)
            
        # Check for game quit condition
        if self.input_system.should_quit:
            self.running = False
            
        # Check game over condition
        if self.turn_scheduler.game_state == GameState.GAME_OVER:
            # Game over handling would go here
            # For now, just print a message and keep running
            add_message("Game Over!", (255, 50, 50))
            print("Game Over!")
            # self.running = False
    
    def run(self) -> None:
        """
        Run the main game loop
        """
        # Initialize the game
        self.initialize_game()
        
        # Set all entities to be able to act on the first turn
        self._activate_all_entities_for_first_turn()
        
        # Main game loop
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(60) / 1000.0
            
            # Update the game
            self.update(dt)
            
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
        
        # Clean up and quit
        pygame.quit()
        sys.exit()
        
    def _register_event_listeners(self) -> None:
        """
        Register event listeners for game events
        """
        # Add combat system event listeners
        self.combat_system.add_attack_hit_listener(
            lambda em, attacker, defender, damage: None  # Already handled by internal logging
        )
        
        self.combat_system.add_entity_death_listener(
            lambda em, entity, killer: self._handle_entity_death(em, entity, killer)
        )
    
    def _handle_entity_death(self, entity_manager, entity_id, killer_id) -> None:
        """
        Handle entity death event
        
        Args:
            entity_manager: The entity manager
            entity_id: ID of the entity that died
            killer_id: ID of the entity that killed it (if any)
        """
        from components.player_tag import PlayerTag
        
        # Check if it's the player
        if entity_manager.has_component(entity_id, PlayerTag):
            # Player died, game over
            self.turn_scheduler.set_game_over()
    
    def _activate_all_entities_for_first_turn(self) -> None:
        """
        Activate all entities for the first turn to ensure they can act
        """
        from utils.debug import debug_print
        from components.turn_state import TurnState
        
        # Get all entities with the TurnState component
        entities_with_turn_state = self.entity_manager.get_entities_with_components([TurnState])
        debug_print("GameLoop", f"Setting up initial turn states for {len(entities_with_turn_state)} entities")
        
        # Set all entities to can_act=True for the first turn
        for entity_id in entities_with_turn_state:
            turn_state = self.entity_manager.get_component(entity_id, TurnState)
            if turn_state:
                turn_state.set_can_act(True)
                debug_print("GameLoop", f"Activated entity {entity_id} for first turn")
