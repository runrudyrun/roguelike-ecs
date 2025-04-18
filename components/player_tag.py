"""
Player Tag component for the ECS architecture.
Marks an entity as the player character.
"""

class PlayerTag:
    """Component that tags an entity as the player character"""
    
    def __init__(self):
        """
        Initialize a player tag component.
        This is a simple tag component with no additional data.
        """
        pass
    
    def __str__(self) -> str:
        return "PlayerTag()"
