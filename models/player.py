"""
Player class for the NFL Football Simulation
"""
import random


class Player:
    """Represents a player with stats and attributes"""

    def __init__(self, name, position, skill, age, durability=95):
        self.name = name
        self.position = position
        self.skill = skill
        self.age = age
        self.durability = durability
        self.years_played = 0
        self.retired = False

        # Offensive stats
        self.pass_attempts = 0
        self.pass_completions = 0
        self.pass_yards = 0
        self.pass_td = 0
        self.interceptions = 0
        self.longest_pass = 0
        self.sacks_taken = 0

        self.rush_attempts = 0
        self.rush_yards = 0
        self.rush_td = 0
        self.longest_rush = 0
        self.fumbles = 0

        self.rec_targets = 0
        self.rec_catches = 0
        self.rec_yards = 0
        self.rec_td = 0
        self.drops = 0
        self.longest_rec = 0

        # Defensive stats
        self.tackles = 0
        self.sacks = 0
        self.qb_pressure = 0
        self.interceptions_def = 0
        self.forced_fumbles = 0
        self.fumble_recoveries = 0
        self.pass_deflections = 0

        # Career stats (accumulated across all seasons)
        self.career_stats = {
            "pass_attempts": 0, "pass_completions": 0, "pass_yards": 0, "pass_td": 0,
            "interceptions": 0, "longest_pass": 0, "sacks_taken": 0,
            "rush_attempts": 0, "rush_yards": 0, "rush_td": 0, "longest_rush": 0, "fumbles": 0,
            "rec_targets": 0, "rec_catches": 0, "rec_yards": 0, "rec_td": 0,
            "drops": 0, "longest_rec": 0,
            "tackles": 0, "sacks": 0, "qb_pressure": 0, "interceptions_def": 0,
            "forced_fumbles": 0, "fumble_recoveries": 0, "pass_deflections": 0
        }

        self.reset_stats()

    def reset_stats(self):
        """Reset all stats to zero"""
        attrs = [
            "pass_attempts", "pass_completions", "pass_yards", "pass_td", "interceptions",
            "longest_pass", "sacks_taken", "rush_attempts", "rush_yards", "rush_td",
            "longest_rush", "fumbles", "rec_targets", "rec_catches", "rec_yards", "rec_td",
            "drops", "longest_rec", "tackles", "sacks", "qb_pressure", "interceptions_def",
            "forced_fumbles", "fumble_recoveries", "pass_deflections"
        ]
        for attr in attrs:
            setattr(self, attr, 0)

    def progress(self):
        """Age player and adjust skill based on age"""
        if self.retired:
            return

        if self.age <= 25:
            change = random.randint(0, 3)
        elif self.age <= 29:
            change = random.randint(-1, 2)
        else:
            change = random.randint(-3, 1)

        self.skill = max(50, min(99, self.skill + change))
        self.age += 1
        self.years_played += 1

    def should_retire(self):
        """Determine if player should retire based on age"""
        return self.age >= 35

    def accumulate_career_stats(self):
        """Add current season stats to career totals"""
        stat_attrs = [
            "pass_attempts", "pass_completions", "pass_yards", "pass_td", "interceptions",
            "sacks_taken", "rush_attempts", "rush_yards", "rush_td", "fumbles",
            "rec_targets", "rec_catches", "rec_yards", "rec_td", "drops",
            "tackles", "sacks", "qb_pressure", "interceptions_def",
            "forced_fumbles", "fumble_recoveries", "pass_deflections"
        ]

        for attr in stat_attrs:
            self.career_stats[attr] += getattr(self, attr, 0)

        # Handle longest stats (take the max)
        if self.longest_pass > self.career_stats.get("longest_pass", 0):
            self.career_stats["longest_pass"] = self.longest_pass
        if self.longest_rush > self.career_stats.get("longest_rush", 0):
            self.career_stats["longest_rush"] = self.longest_rush
        if self.longest_rec > self.career_stats.get("longest_rec", 0):
            self.career_stats["longest_rec"] = self.longest_rec
