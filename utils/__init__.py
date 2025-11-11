"""
Utilities package for NFL Football Simulation
"""
from .data_loader import load_rosters_from_excel, create_new_league
from .stats import (
    get_ordinal, get_team_summary, print_team_summary,
    print_team_stats, print_last_game_stats, print_opponent_preview,
    calculate_team_ratings, print_career_stats, view_last_game_plays,
    calculate_team_stats, get_top_players
)
from .standings import view_standings
from .save_load import save_franchise, load_franchise
from .draft import (
    generate_draft_prospects, run_scouting, run_draft,
    view_draft_prospects, calculate_draft_order
)

__all__ = [
    'load_rosters_from_excel', 'create_new_league',
    'get_ordinal', 'get_team_summary', 'print_team_summary',
    'print_team_stats', 'print_last_game_stats', 'print_opponent_preview',
    'calculate_team_ratings', 'print_career_stats', 'view_last_game_plays',
    'calculate_team_stats', 'get_top_players',
    'view_standings',
    'save_franchise', 'load_franchise',
    'generate_draft_prospects', 'run_scouting', 'run_draft',
    'view_draft_prospects', 'calculate_draft_order'
]
