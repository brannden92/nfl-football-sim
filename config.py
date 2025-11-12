"""
Configuration constants for the NFL Football Simulation
"""

# Franchise settings
FRANCHISE_LENGTH = 40  # Number of seasons in a franchise
SEASON_GAMES = 18      # Number of regular season weeks (17 games + BYE week per team)

# Team abbreviations (proper NFL abbreviations)
TEAM_ABBREVIATIONS = {
    "Arizona Cardinals": "ARI",
    "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR",
    "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN",
    "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN",
    "Detroit Lions": "DET",
    "Green Bay Packers": "GB",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV",
    "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR",
    "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN",
    "New England Patriots": "NE",
    "New Orleans Saints": "NO",
    "New York Giants": "NYG",
    "New York Jets": "NYJ",
    "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA",
    "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",
    "Washington Commanders": "WAS"
}

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
    "forced_fumbles", "fumble_recoveries", "pass_deflections",
    # Kicking
    "fg_attempts", "fg_made", "longest_fg", "xp_attempts", "xp_made",
    # Punting
    "punt_attempts", "punt_yards", "longest_punt", "inside_20",
    # Returns
    "kickoff_returns", "kickoff_return_yards", "longest_kickoff_return",
    "punt_returns", "punt_return_yards", "longest_punt_return"
]
