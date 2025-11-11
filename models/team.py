"""
Team class for the NFL Football Simulation
"""


class Team:
    """Represents a football team with players and stats"""

    def __init__(self, name):
        self.name = name
        self.players = []
        self.qb_starters = []
        self.rb_starters = []
        self.wr_starters = []
        self.te_starters = []
        self.defense_starters = []
        self.score = 0
        self.wins = 0
        self.losses = 0
        self.points_for = 0
        self.points_against = 0
        self.league = None
        self.division = None
        self.last_game_stats = {}

    def reset_score(self):
        """Reset the team's current score to 0"""
        self.score = 0

    def reset_weekly_stats(self):
        """Reset all player stats for the week"""
        for p in self.players:
            p.reset_stats()
