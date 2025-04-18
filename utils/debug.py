"""
Debug utilities for tracking system execution and entity states.
"""

# Flag to enable/disable debug output
DEBUG_ENABLED = True

def debug_print(system_name: str, message: str) -> None:
    """
    Print a debug message if debugging is enabled
    
    Args:
        system_name: Name of the system printing the message
        message: Debug message to print
    """
    if DEBUG_ENABLED:
        print(f"[DEBUG:{system_name}] {message}")
