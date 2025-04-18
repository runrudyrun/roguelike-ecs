"""
Message logging utility for the ECS architecture.
Provides a centralized way to log messages to the UI.
"""
from typing import Tuple, Optional, Dict, List, Callable
import time

from utils.debug import debug_print


class MessageLog:
    """
    Singleton message logging utility for the game.
    Provides a way for any system to log messages to the UI log.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageLog, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize the message log"""
        self._ui_system = None
        self._entity_manager = None
        self._messages_buffer: List[Tuple[str, Tuple[int, int, int]]] = []
        self._last_flush_time = time.time()
        debug_print("MessageLog", "Message log initialized")
    
    def register_ui_system(self, ui_system: 'UISystem', entity_manager: 'EntityManager') -> None:
        """
        Register the UI system with the message log.
        This allows the message log to forward messages to the UI.
        
        Args:
            ui_system: UI system to register
            entity_manager: Entity manager reference
        """
        self._ui_system = ui_system
        self._entity_manager = entity_manager
        
        # Flush any queued messages
        self._flush_messages()
        debug_print("MessageLog", "UI system registered")
    
    def log(self, message: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """
        Log a message to the UI.
        If the UI system is not registered yet, the message will be buffered.
        
        Args:
            message: Message to log
            color: Color of the message (RGB tuple)
        """
        # Always log to console for debugging
        debug_print("MessageLog", f"Message: {message}")
        
        if self._ui_system and self._entity_manager:
            try:
                self._ui_system.log_message(self._entity_manager, message, color)
                debug_print("MessageLog", f"Sent message to UI: {message}")
            except Exception as e:
                debug_print("MessageLog", f"Error sending message to UI: {e}")
                # Buffer the message in case of error
                self._messages_buffer.append((message, color))
        else:
            # Buffer the message until the UI system is registered
            self._messages_buffer.append((message, color))
            debug_print("MessageLog", f"Buffered message: {message} (UI system not registered)")
            
            # Try to flush buffered messages periodically
            current_time = time.time()
            if current_time - self._last_flush_time > 2.0:
                self._flush_messages()
                self._last_flush_time = current_time
    
    def _flush_messages(self) -> None:
        """Flush any buffered messages to the UI system"""
        if not self._ui_system or not self._entity_manager:
            debug_print("MessageLog", "Cannot flush messages - UI system or entity manager not registered")
            return
        
        if not self._messages_buffer:
            return
            
        debug_print("MessageLog", f"Attempting to flush {len(self._messages_buffer)} buffered messages")
        flushed_count = 0
            
        try:
            for message, color in self._messages_buffer:
                self._ui_system.log_message(self._entity_manager, message, color)
                flushed_count += 1
            
            debug_print("MessageLog", f"Successfully flushed {flushed_count} buffered messages")
            self._messages_buffer.clear()
        except Exception as e:
            debug_print("MessageLog", f"Error flushing messages: {e}")
            # If there was an error, remove any successfully flushed messages
            if flushed_count > 0:
                self._messages_buffer = self._messages_buffer[flushed_count:]


# Create a singleton instance
message_log = MessageLog()

# Convenience function
def log_message(message: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
    """
    Convenience function to log a message to the UI
    
    Args:
        message: Message to log
        color: Color of the message (RGB tuple)
    """
    message_log.log(message, color)
