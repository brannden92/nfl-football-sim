"""
Configuration constants for the NFL Football Simulation
"""

# Franchise settings
FRANCHISE_LENGTH = 40  # Number of seasons in a franchise
SEASON_GAMES = 17      # Number of regular season games

# Stat attributes tracked for players
STAT_ATTRS = [
    # Passing
    "pass_attempts", "pass_completions", "pass_yards", "pass_td",
    "interceptions", "longest_pass", "sacks_taken",
    # Rushing
    "rush_attempts", "rush_yards", "rush_td", "longest_rush", "fumbles",
    # Receiving
    "rec_targets", "rec_catches", "rec_yards", "rec_td", "drops", "longest_rec",
    # Defense
    "tackles", "sacks", "qb_pressure", "interceptions_def",
    "forced_fumbles", "fumble_recoveries", "pass_deflections"
]
