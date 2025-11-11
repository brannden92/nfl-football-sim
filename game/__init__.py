"""
Game simulation package for NFL Football Simulation
"""
from .simulation import simulate_play, simulate_drive, simulate_game
from .playoffs import run_playoffs, get_playoff_teams

__all__ = ['simulate_play', 'simulate_drive', 'simulate_game', 'run_playoffs', 'get_playoff_teams']
