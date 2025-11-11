# NFL Football Simulation

A Python-based NFL franchise simulation game with realistic stats, player progression, and playoff systems.

## Project Structure

```
nfl-football-sim/
├── config.py                    # Game configuration constants
├── main.py                      # Main entry point - run this to play
├── models/                      # Data models
│   ├── __init__.py
│   ├── player.py               # Player class with stats and progression
│   ├── team.py                 # Team class with roster management
│   ├── franchise.py            # Franchise class for multi-season play
│   └── game_clock.py           # Game clock management
├── game/                        # Game simulation logic
│   ├── __init__.py
│   ├── simulation.py           # Play-by-play simulation
│   └── playoffs.py             # Playoff bracket and logic
├── utils/                       # Utility functions
│   ├── __init__.py
│   ├── data_loader.py          # Load rosters from Excel
│   ├── stats.py                # Statistics display functions
│   ├── standings.py            # League standings display
│   └── save_load.py            # Save/load franchise data
├── fake_nfl_rosters.xlsx       # Team rosters data
└── football_sim.py             # Original monolithic file (backup)

```

## How to Run

```bash
python main.py
```

## Features

- Full 32-team NFL league with realistic divisions
- Play-by-play game simulation with passing, rushing, and defensive stats
- Player progression and retirement system
- 40-season franchise mode
- Playoff bracket (Wild Card, Divisional, Conference Championships, Super Bowl)
- Save/load functionality
- Detailed statistics tracking (season and per-game)

## Code Organization

### Models
- **Player**: Individual player with stats, skills, and progression
- **Team**: Team with roster and standings
- **Franchise**: Multi-season franchise management
- **GameClock**: Game time tracking

### Game Simulation
- **simulation.py**: Core play simulation logic (plays, drives, games)
- **playoffs.py**: Playoff seeding and tournament execution

### Utilities
- **data_loader.py**: Load team rosters from Excel
- **stats.py**: Display player and team statistics
- **standings.py**: Display league standings
- **save_load.py**: Pickle-based save/load system

## Configuration

Edit `config.py` to modify:
- `FRANCHISE_LENGTH`: Number of seasons (default: 40)
- `SEASON_GAMES`: Games per season (default: 17)
- `STAT_ATTRS`: Tracked player statistics
