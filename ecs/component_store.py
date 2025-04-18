"""
Component Store module for the ECS architecture.
Stores and manages all component instances for entities.
"""
from typing import Dict, Set, Type, List, Any

class ComponentStore:
    """Stores all components for entities in an optimized way"""
    
    def __init__(self):
        # Dictionary mapping component types to a dictionary of entity_id -> component
        self._component_stores: Dict[Type, Dict[int, Any]] = {}
        # Dictionary mapping entity_id to a set of component types
        self._entity_components: Dict[int, Set[Type]] = {}
        # Dictionary to store system instances by type name
        self._systems: Dict[str, Any] = {}
    
    def add_component(self, entity_id: int, component: Any) -> None:
        """Add a component to an entity"""
        component_type = type(component)
        
        # Ensure we have a store for this component type
        if component_type not in self._component_stores:
            self._component_stores[component_type] = {}
        
        # Add the component to the store
        self._component_stores[component_type][entity_id] = component
        
        # Track that this entity has this component type
        if entity_id not in self._entity_components:
            self._entity_components[entity_id] = set()
        self._entity_components[entity_id].add(component_type)
    
    def remove_component(self, entity_id: int, component_type: Type) -> None:
        """Remove a component from an entity"""
        if (component_type in self._component_stores and 
            entity_id in self._component_stores[component_type]):
            # Remove from component store
            del self._component_stores[component_type][entity_id]
            
            # Remove from entity tracking
            if entity_id in self._entity_components:
                self._entity_components[entity_id].discard(component_type)
                
                # Clean up empty sets
                if not self._entity_components[entity_id]:
                    del self._entity_components[entity_id]
    
    def remove_all_components(self, entity_id: int) -> None:
        """Remove all components for an entity"""
        if entity_id in self._entity_components:
            component_types = list(self._entity_components[entity_id])
            for component_type in component_types:
                self.remove_component(entity_id, component_type)
            del self._entity_components[entity_id]
    
    def has_component(self, entity_id: int, component_type: Type) -> bool:
        """Check if an entity has a specific component"""
        return (component_type in self._component_stores and 
                entity_id in self._component_stores[component_type])
    
    def get_component(self, entity_id: int, component_type: Type) -> Any:
        """Get a component for an entity"""
        if self.has_component(entity_id, component_type):
            return self._component_stores[component_type][entity_id]
        return None
    
    def get_all_components(self, entity_id: int) -> Dict[Type, Any]:
        """Get all components for an entity"""
        if entity_id not in self._entity_components:
            return {}
        
        result = {}
        for component_type in self._entity_components[entity_id]:
            result[component_type] = self._component_stores[component_type][entity_id]
        return result
    
    def get_entities_with_components(self, component_types: List[Type]) -> Set[int]:
        """Get all entities that have all the specified component types"""
        if not component_types:
            return set()
        
        # Get the entities that have the first component type
        if component_types[0] not in self._component_stores:
            return set()
        
        # Start with the entities that have the first component type
        result = set(self._component_stores[component_types[0]].keys())
        
        # Filter for entities that have all other component types
        for component_type in component_types[1:]:
            if component_type not in self._component_stores:
                return set()
            
            # Keep only entities that also have this component type
            result &= set(self._component_stores[component_type].keys())
            
            # Short-circuit if no entities left
            if not result:
                return set()
        
        return result
    
    def get_component_store_for_type(self, component_type: Type) -> Dict[int, Any]:
        """Get the component store for a specific component type"""
        return self._component_stores.get(component_type, {})
    
    def register_system(self, system: Any) -> None:
        """Register a system with the component store"""
        system_type = type(system).__name__
        self._systems[system_type] = system
    
    def get_system(self, system_type_name: str) -> Any:
        """Get a system by its type name"""
        return self._systems.get(system_type_name)
