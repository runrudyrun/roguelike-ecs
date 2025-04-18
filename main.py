"""
Main entry point for the Roguelike ECS game.
"""
import pygame
from game.game_loop import GameLoop

def main():
    """Main entry point for the game"""
    # Game window settings
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    TILE_SIZE = 20
    
    # Create and run the game loop
    game = GameLoop(SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
    game.run()

if __name__ == "__main__":
    main()
