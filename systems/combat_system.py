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
            
            # Notify hit listeners
            for listener in self._on_attack_hit:
                listener(entity_manager, attacker_id, defender_id, damage)
            
            # If the defender was killed, notify death listeners
            if killed:
                for listener in self._on_entity_death:
                    listener(entity_manager, defender_id, attacker_id)
        else:
            # Notify miss listeners
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
