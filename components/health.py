"""
Health component for the ECS architecture.
Represents the health status of an entity.
"""

class Health:
    """Component representing the health status of an entity"""
    
    def __init__(self, current: int, max_health: int):
        self.current = current
        self.max = max_health
        self.is_dead = False
    
    def take_damage(self, amount: int) -> bool:
        """
        Apply damage to this entity
        
        Args:
            amount: Amount of damage to take
            
        Returns:
            True if the entity died from this damage, False otherwise
        """
        self.current = max(0, self.current - amount)
        
        if self.current <= 0 and not self.is_dead:
            self.is_dead = True
            return True
        
        return False
    
    def heal(self, amount: int) -> None:
        """
        Heal this entity
        
        Args:
            amount: Amount of health to restore
        """
        if self.is_dead:
            return
            
        self.current = min(self.max, self.current + amount)
    
    def is_alive(self) -> bool:
        """Check if the entity is alive"""
        return not self.is_dead
    
    def get_health_percentage(self) -> float:
        """Get the current health as a percentage"""
        if self.max <= 0:
            return 0.0
        return self.current / self.max
    
    def __str__(self) -> str:
        return f"Health({self.current}/{self.max})"
