"""
Main entry point for the Roguelike ECS game.
"""
import pygame
import argparse
from game.game_loop import GameLoop

def main():
    """Main entry point for the game"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Roguelike ECS Game')
    parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
    args = parser.parse_args()
    
    # Game window settings
    SCREEN_WIDTH = 1200  # Increased from 800
    SCREEN_HEIGHT = 600
    TILE_SIZE = 20
    
    # Create and run the game loop
    game = GameLoop(SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, fullscreen=args.fullscreen)
    game.run()

if __name__ == "__main__":
    main()
