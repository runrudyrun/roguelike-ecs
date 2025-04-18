"""
Entity Manager module for the ECS architecture.
Responsible for creating, tracking and destroying entities.
"""
from typing import Dict, Set, Type, List, Optional, Any
from .component_store import ComponentStore

class EntityManager:
    """Manages entities and their components"""
    
    def __init__(self):
        self._next_entity_id = 0
        self._entities: Set[int] = set()
        self._component_store = ComponentStore()
        self._entities_pending_deletion: Set[int] = set()
        
    def create_entity(self) -> int:
        """Create a new entity and return its ID"""
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        self._entities.add(entity_id)
        return entity_id
    
    def destroy_entity(self, entity_id: int) -> None:
        """Mark an entity for deletion at the end of the current frame"""
        if entity_id in self._entities:
            self._entities_pending_deletion.add(entity_id)
    
    def cleanup_entities(self) -> None:
        """Remove all entities marked for deletion"""
        for entity_id in self._entities_pending_deletion:
            if entity_id in self._entities:
                self._entities.remove(entity_id)
                self._component_store.remove_all_components(entity_id)
        self._entities_pending_deletion.clear()
    
    def add_component(self, entity_id: int, component: Any) -> None:
        """Add a component to an entity"""
        if entity_id in self._entities:
            self._component_store.add_component(entity_id, component)
    
    def remove_component(self, entity_id: int, component_type: Type) -> None:
        """Remove a component from an entity"""
        if entity_id in self._entities:
            self._component_store.remove_component(entity_id, component_type)
    
    def has_component(self, entity_id: int, component_type: Type) -> bool:
        """Check if an entity has a specific component"""
        if entity_id in self._entities:
            return self._component_store.has_component(entity_id, component_type)
        return False
    
    def get_component(self, entity_id: int, component_type: Type) -> Any:
        """Get a component from an entity"""
        if entity_id in self._entities:
            return self._component_store.get_component(entity_id, component_type)
        return None
    
    def get_all_components(self, entity_id: int) -> Dict[Type, Any]:
        """Get all components for an entity"""
        if entity_id in self._entities:
            return self._component_store.get_all_components(entity_id)
        return {}
    
    def get_entities_with_components(self, component_types: List[Type]) -> Set[int]:
        """Get all entities that have all the specified component types"""
        return self._component_store.get_entities_with_components(component_types)
    
    def get_component_store(self) -> ComponentStore:
        """Get the component store"""
        return self._component_store
    
    def entity_exists(self, entity_id: int) -> bool:
        """Check if an entity exists"""
        return entity_id in self._entities
    
    def get_entity_count(self) -> int:
        """Get the total number of entities"""
        return len(self._entities)
