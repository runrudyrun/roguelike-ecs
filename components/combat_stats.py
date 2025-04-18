"""
Combat Stats component for the ECS architecture.
Represents an entity's combat capabilities.
"""

class CombatStats:
    """Component representing combat capabilities of an entity"""
    
    def __init__(self, attack: int, defense: int, power: int = 0):
        """
        Initialize combat stats
        
        Args:
            attack: Attack value - affects hit chance
            defense: Defense value - reduces damage taken
            power: Power value - affects damage dealt
        """
        self.attack = attack
        self.defense = defense
        self.power = power
    
    def calculate_damage(self, target_defense: int) -> int:
        """
        Calculate damage against a target with given defense
        
        Args:
            target_defense: The defense value of the target
            
        Returns:
            The calculated damage amount
        """
        # Simple damage formula: power - (defense / 2)
        damage = max(0, self.power - (target_defense // 2))
        return max(1, damage)  # Minimum damage of 1
    
    def __str__(self) -> str:
        return f"CombatStats(attack={self.attack}, defense={self.defense}, power={self.power})"
