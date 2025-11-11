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

        # Draft and scouting system
        self.scouting_points = 100  # Points to invest in scouting draft prospects
        self.draft_prospects = []   # List of draft prospect players
        self.scouting_investment = {}  # Dict mapping prospect name to scout points invested
