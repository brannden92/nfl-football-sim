"""
Franchise class for the NFL Football Simulation
"""


class Franchise:
    """Represents a franchise with multiple teams across seasons"""

    def __init__(self, teams, user_team_name, current_season=1, current_week=1):
        self.teams = teams
        self.user_team_name = user_team_name
        self.current_season = current_season
        self.current_week = current_week
