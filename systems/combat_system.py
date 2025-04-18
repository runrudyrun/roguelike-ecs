"""
Combat System module for the ECS architecture.
Handles combat interactions between entities.
"""
import random
from typing import Optional, Callable, Dict, List, Tuple

from ecs.system import System
from ecs.entity_manager import EntityManager
from components.position import Position
from components.combat_stats import CombatStats
from components.health import Health
from components.ai_intent import AIIntent, ActionType
from components.turn_state import TurnState
from utils.debug import debug_print
from utils.message_queue import add_message

class CombatSystem(System):
    """System responsible for handling combat between entities"""
    
    def __init__(self):
        """Initialize the combat system"""
        super().__init__()
        
        # Required components for this system
        self._required_component_types = [CombatStats, Health]
        
        # Set a moderate priority
        self._priority = 10
        
        # Event listeners for combat events
        self._on_attack_hit: List[Callable] = []
        self._on_attack_miss: List[Callable] = []
        self._on_entity_death: List[Callable] = []
    
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Process all pending combat actions
        
        Args:
            entity_manager: The entity manager
            dt: Delta time since last update
        """
        # Get all entities with AI intent for attack
        ai_entities = entity_manager.get_entities_with_components([AIIntent, Position])
        
        for entity_id in ai_entities:
            # Check if this entity has a TurnState and can act
            turn_state = entity_manager.get_component(entity_id, TurnState)
            if turn_state is None or not turn_state.can_act:
                # Skip entities that can't act this turn
                continue
                
            ai_intent = entity_manager.get_component(entity_id, AIIntent)
            
            # Process attack intents
            if ai_intent.action_type == ActionType.ATTACK and ai_intent.target_entity is not None:
                target_id = ai_intent.target_entity
                
                # Perform the attack
                self.perform_attack(entity_manager, entity_id, target_id)
                
                # Clear the intent after processing
                ai_intent.clear_intent()
                
                # Mark this entity as having acted this turn
                turn_state.set_can_act(False)
    
    def perform_attack(self, entity_manager: EntityManager, 
                      attacker_id: int, defender_id: int) -> bool:
        """
        Perform an attack from one entity to another
        
        Args:
            entity_manager: The entity manager
            attacker_id: ID of the attacking entity
            defender_id: ID of the defending entity
            
        Returns:
            True if the attack hit, False if it missed
        """
        # Ensure both entities exist and have the required components
        if not (entity_manager.entity_exists(attacker_id) and 
                entity_manager.entity_exists(defender_id)):
            return False
        
        attacker_stats = entity_manager.get_component(attacker_id, CombatStats)
        defender_stats = entity_manager.get_component(defender_id, CombatStats)
        defender_health = entity_manager.get_component(defender_id, Health)
        
        if not (attacker_stats and defender_stats and defender_health):
            return False
        
        # Calculate hit chance
        hit_chance = self._calculate_hit_chance(attacker_stats.attack, defender_stats.defense)
        
        # Roll for hit
        roll = random.random()
        hit = roll <= hit_chance
        
        if hit:
            # Calculate damage
            damage = attacker_stats.calculate_damage(defender_stats.defense)
            
            # Apply damage to defender
            killed = defender_health.take_damage(damage)
            
            # Log the attack
            self._log_attack_hit(entity_manager, attacker_id, defender_id, damage)
            
            # Notify hit listeners
            for listener in self._on_attack_hit:
                listener(entity_manager, attacker_id, defender_id, damage)
            
            # If the defender was killed, log it and notify death listeners
            if killed:
                self._log_entity_death(entity_manager, defender_id, attacker_id)
                for listener in self._on_entity_death:
                    listener(entity_manager, defender_id, attacker_id)
        else:
            # Log the miss and notify miss listeners
            self._log_attack_miss(entity_manager, attacker_id, defender_id)
            for listener in self._on_attack_miss:
                listener(entity_manager, attacker_id, defender_id)
        
        return hit
    
    def _calculate_hit_chance(self, attack: int, defense: int) -> float:
        """
        Calculate the chance to hit based on attack and defense values
        
        Args:
            attack: Attack value of the attacker
            defense: Defense value of the defender
            
        Returns:
            Probability (0.0 to 1.0) of the attack hitting
        """
        # Simple formula: base 60% chance, +2% per attack point, -2% per defense point
        hit_chance = 0.6 + (attack * 0.02) - (defense * 0.02)
        
        # Clamp between 10% and 95%
        return max(0.1, min(0.95, hit_chance))
    
    def can_attack(self, entity_manager: EntityManager, attacker_id: int, 
                  defender_id: int) -> bool:
        """
        Check if an entity can attack another entity
        
        Args:
            entity_manager: The entity manager
            attacker_id: ID of the potential attacker
            defender_id: ID of the potential defender
            
        Returns:
            True if the attack is possible, False otherwise
        """
        # Ensure both entities exist and have the required components
        if not (entity_manager.entity_exists(attacker_id) and 
                entity_manager.entity_exists(defender_id)):
            return False
        
        # Check for required components
        attacker_stats = entity_manager.get_component(attacker_id, CombatStats)
        defender_health = entity_manager.get_component(defender_id, Health)
        
        if not (attacker_stats and defender_health):
            return False
        
        # Check if defender is alive
        if not defender_health.is_alive():
            return False
        
        # Check if entities are adjacent (assuming they need to be for melee)
        attacker_pos = entity_manager.get_component(attacker_id, Position)
        defender_pos = entity_manager.get_component(defender_id, Position)
        
        if not (attacker_pos and defender_pos):
            return False
        
        # Calculate Manhattan distance
        distance = abs(attacker_pos.x - defender_pos.x) + abs(attacker_pos.y - defender_pos.y)
        
        # Return true if adjacent (distance == 1)
        return distance == 1
    
    def add_attack_hit_listener(self, listener: Callable) -> None:
        """Add a listener for attack hit events"""
        self._on_attack_hit.append(listener)
    
    def add_attack_miss_listener(self, listener: Callable) -> None:
        """Add a listener for attack miss events"""
        self._on_attack_miss.append(listener)
    
    def add_entity_death_listener(self, listener: Callable) -> None:
        """Add a listener for entity death events"""
        self._on_entity_death.append(listener)
    
    def _log_attack_hit(self, entity_manager: EntityManager, attacker_id: int, defender_id: int, damage: int) -> None:
        """Log an attack hit message"""
        from components.player_tag import PlayerTag
        
        # Get entity names or descriptions
        attacker_is_player = entity_manager.has_component(attacker_id, PlayerTag)
        defender_is_player = entity_manager.has_component(defender_id, PlayerTag)
        
        # Format message based on who's attacking whom
        if attacker_is_player:
            message = f"You hit the enemy for {damage} damage!"
            color = (150, 255, 150)  # Light green for player success
        elif defender_is_player:
            message = f"Enemy hits you for {damage} damage!"
            color = (255, 150, 150)  # Light red for player taking damage
        else:
            message = f"Enemy attacks another enemy for {damage} damage."
            color = (200, 200, 200)  # Gray for non-player combat
        
        # Log the message
        add_message(message, color)
        debug_print("CombatSystem", message)
    
    def _log_attack_miss(self, entity_manager: EntityManager, attacker_id: int, defender_id: int) -> None:
        """Log an attack miss message"""
        from components.player_tag import PlayerTag
        
        # Get entity names or descriptions
        attacker_is_player = entity_manager.has_component(attacker_id, PlayerTag)
        defender_is_player = entity_manager.has_component(defender_id, PlayerTag)
        
        # Format message based on who's attacking whom
        if attacker_is_player:
            message = "Your attack misses!"
            color = (200, 200, 200)  # Gray for miss
        elif defender_is_player:
            message = "Enemy's attack misses you!"
            color = (200, 220, 255)  # Light blue for player dodging
        else:
            message = "Enemy misses another enemy."
            color = (180, 180, 180)  # Gray for non-player combat
        
        # Log the message
        add_message(message, color)
        debug_print("CombatSystem", message)
    
    def _log_entity_death(self, entity_manager: EntityManager, entity_id: int, killer_id: Optional[int] = None) -> None:
        """Log an entity death message"""
        from components.player_tag import PlayerTag
        
        # Check if player is involved
        entity_is_player = entity_manager.has_component(entity_id, PlayerTag)
        killer_is_player = killer_id is not None and entity_manager.has_component(killer_id, PlayerTag)
        
        # Format message based on who died
        if entity_is_player:
            message = "You have died! Game over."
            color = (255, 50, 50)  # Bright red for player death
        elif killer_is_player:
            message = "You killed an enemy!"
            color = (255, 255, 150)  # Yellow for kill
        else:
            message = "An enemy has died."
            color = (180, 180, 180)  # Gray for non-player death
        
        # Log the message
        add_message(message, color)
        debug_print("CombatSystem", message)
