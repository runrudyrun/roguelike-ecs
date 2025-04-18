"""
Message Queue module for the roguelike ECS game.
Provides a centralized way to log and display game messages.
"""
from typing import List, Tuple, Optional
from collections import deque


class MessageQueue:
    """
    Singleton class for managing game messages in a classic roguelike style.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageQueue, cls).__new__(cls)
            cls._instance._messages = deque(maxlen=50)  # Store up to 50 messages
        return cls._instance
    
    def add_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Add a message to the queue with a color"""
        self._messages.append((text, color))
        # Print to console for debugging
        print(f"LOG: {text}")
    
    def get_messages(self, count: int = 10) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Get the most recent messages, newest last"""
        return list(self._messages)[-count:]


# Create a singleton instance
message_queue = MessageQueue()

# Convenience functions
def add_message(text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
    """Add a message to the global message queue"""
    message_queue.add_message(text, color)

def get_messages(count: int = 10) -> List[Tuple[str, Tuple[int, int, int]]]:
    """Get recent messages from the global message queue"""
    return message_queue.get_messages(count)
