"""
System base module for the ECS architecture.
Defines the interface for all game systems.
"""
from abc import ABC, abstractmethod
from typing import List, Type, Set
from .entity_manager import EntityManager

class System(ABC):
    """
    Base class for all systems in the ECS architecture.
    Systems contain game logic and operate on entities with specific components.
    """
    
    def __init__(self):
        # The types of components this system requires
        self._required_component_types: List[Type] = []
        # Priority determines the order of system execution (lower runs first)
        self._priority: int = 0
    
    @property
    def priority(self) -> int:
        """Get the system priority"""
        return self._priority
    
    @priority.setter
    def priority(self, value: int) -> None:
        """Set the system priority"""
        self._priority = value
    
    @property
    def required_component_types(self) -> List[Type]:
        """Get the component types this system requires"""
        return self._required_component_types
    
    def get_relevant_entities(self, entity_manager: EntityManager) -> Set[int]:
        """Get all entities that have the required components for this system"""
        if not self._required_component_types:
            return set()
        return entity_manager.get_entities_with_components(self._required_component_types)
    
    @abstractmethod
    def update(self, entity_manager: EntityManager, dt: float) -> None:
        """
        Update this system for the current frame
        
        Args:
            entity_manager: The entity manager containing all entities and components
            dt: Delta time in seconds since last update
        """
        pass


class SystemRegistry:
    """
    Manages all systems and their execution order.
    """
    
    def __init__(self):
        self._systems: List[System] = []
        self._initialized = False
        self._entity_manager = None
    
    def add_system(self, system: System) -> None:
        """Add a system to the registry"""
        self._systems.append(system)
        self._initialized = False
        
        # If we have an entity manager, register the system with it
        if self._entity_manager:
            self._register_system_with_entity_manager(system)
    
    def remove_system(self, system: System) -> None:
        """Remove a system from the registry"""
        if system in self._systems:
            self._systems.remove(system)
            self._initialized = False
    
    def set_entity_manager(self, entity_manager) -> None:
        """Set the entity manager for this system registry"""
        self._entity_manager = entity_manager
        
        # Register all systems with the entity manager
        for system in self._systems:
            self._register_system_with_entity_manager(system)
    
    def _register_system_with_entity_manager(self, system: System) -> None:
        """Register a system with the entity manager's component store"""
        if self._entity_manager:
            component_store = self._entity_manager.get_component_store()
            component_store.register_system(system)
    
    def initialize(self) -> None:
        """Initialize the system registry by sorting systems by priority"""
        self._systems.sort(key=lambda s: s.priority)
        self._initialized = True
    
    def update_all(self, entity_manager: EntityManager, dt: float) -> None:
        """Update all systems in priority order"""
        if not self._initialized:
            self.initialize()
        
        for system in self._systems:
            system.update(entity_manager, dt)
