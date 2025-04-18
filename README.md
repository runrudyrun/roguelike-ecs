# Roguelike ECS Game

A turn-based roguelike game built with a pure Entity-Component-System (ECS) architecture.

## Architecture Overview

- **Entity**: Just an ID, with no data or behavior attached
- **Component**: Pure data structures, with no behavior
- **System**: Contains all game logic and processes entities with specific components

## Features

- Scalable ECS architecture capable of handling thousands of entities
- Turn-based combat system
- Procedural map generation
- Enemy AI with pathfinding
- Flexible component-based design for easy extension

## Getting Started

1. Install the requirements:
```
pip install -r requirements.txt
```

2. Run the game:
```
python main.py
```

## Project Structure

- `ecs/`: Core ECS framework
- `components/`: Component definitions
- `systems/`: Game systems implementing game logic
- `game/`: Game-specific code and main loop
