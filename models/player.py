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

        # Rookie tracking for scouting system
        self.is_rookie = (age <= 22)  # Players 22 or younger are considered rookies
        self.scouting_variance = {}  # Store variance offsets for consistency

        # Core attributes and potentials (affect in-game performance)
        # Initialize based on skill level and position
        self._initialize_attributes_and_potentials()

        # Initialize scouting variance for rookies
        if self.is_rookie:
            self._initialize_scouting_variance()

        # Defensive stats
        self.tackles = 0
        self.sacks = 0
        self.qb_pressure = 0
        self.interceptions_def = 0
        self.forced_fumbles = 0
        self.fumble_recoveries = 0
        self.pass_deflections = 0

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

        # Kicker stats
        self.fg_attempts = 0
        self.fg_made = 0
        self.longest_fg = 0
        self.xp_attempts = 0
        self.xp_made = 0

        # Punter stats
        self.punt_attempts = 0
        self.punt_yards = 0
        self.longest_punt = 0
        self.inside_20 = 0

        # Career stats (accumulated across all seasons)
        self.career_stats = {
            "pass_attempts": 0, "pass_completions": 0, "pass_yards": 0, "pass_td": 0,
            "interceptions": 0, "longest_pass": 0, "sacks_taken": 0,
            "rush_attempts": 0, "rush_yards": 0, "rush_td": 0, "longest_rush": 0, "fumbles": 0,
            "rec_targets": 0, "rec_catches": 0, "rec_yards": 0, "rec_td": 0,
            "drops": 0, "longest_rec": 0,
            "tackles": 0, "sacks": 0, "qb_pressure": 0, "interceptions_def": 0,
            "forced_fumbles": 0, "fumble_recoveries": 0, "pass_deflections": 0,
            "fg_attempts": 0, "fg_made": 0, "longest_fg": 0, "xp_attempts": 0, "xp_made": 0,
            "punt_attempts": 0, "punt_yards": 0, "longest_punt": 0, "inside_20": 0
        }

        self.reset_stats()

    def _initialize_attributes_and_potentials(self):
        """Initialize player attributes and their potentials based on position and skill"""
        # Base variance for randomization
        variance = random.randint(-5, 5)

        # Universal attributes (all positions)
        self.speed = min(99, max(50, self.skill + variance))
        self.speed_potential = min(99, self.speed + random.randint(5, 15))

        self.strength = min(99, max(50, self.skill + variance))
        self.strength_potential = min(99, self.strength + random.randint(5, 15))

        self.awareness = min(99, max(50, self.skill + variance))
        self.awareness_potential = min(99, self.awareness + random.randint(5, 15))

        # Position-specific attributes
        if self.position == "QB":
            self.throw_power = min(99, max(50, self.skill + variance))
            self.throw_power_potential = min(99, self.throw_power + random.randint(5, 15))

            self.throw_accuracy = min(99, max(50, self.skill + variance))
            self.throw_accuracy_potential = min(99, self.throw_accuracy + random.randint(5, 15))

        elif self.position in ["RB", "WR", "TE"]:
            self.catching = min(99, max(50, self.skill + variance))
            self.catching_potential = min(99, self.catching + random.randint(5, 15))

            self.route_running = min(99, max(50, self.skill + variance))
            self.route_running_potential = min(99, self.route_running + random.randint(5, 15))

            if self.position == "RB":
                self.carrying = min(99, max(50, self.skill + variance))
                self.carrying_potential = min(99, self.carrying + random.randint(5, 15))

                self.elusiveness = min(99, max(50, self.skill + variance))
                self.elusiveness_potential = min(99, self.elusiveness + random.randint(5, 15))

        elif self.position == "OL":
            self.pass_blocking = min(99, max(50, self.skill + variance))
            self.pass_blocking_potential = min(99, self.pass_blocking + random.randint(5, 15))

            self.run_blocking = min(99, max(50, self.skill + variance))
            self.run_blocking_potential = min(99, self.run_blocking + random.randint(5, 15))

        elif self.position in ["DL", "LB", "CB", "S"]:
            self.tackling = min(99, max(50, self.skill + variance))
            self.tackling_potential = min(99, self.tackling + random.randint(5, 15))

            self.coverage = min(99, max(50, self.skill + variance))
            self.coverage_potential = min(99, self.coverage + random.randint(5, 15))

            if self.position in ["DL", "LB"]:
                self.pass_rush = min(99, max(50, self.skill + variance))
                self.pass_rush_potential = min(99, self.pass_rush + random.randint(5, 15))

        elif self.position in ["K", "P"]:
            self.kicking_power = min(99, max(50, self.skill + variance))
            self.kicking_power_potential = min(99, self.kicking_power + random.randint(5, 15))

            self.kicking_accuracy = min(99, max(50, self.skill + variance))
            self.kicking_accuracy_potential = min(99, self.kicking_accuracy + random.randint(5, 15))

    def _initialize_scouting_variance(self):
        """Initialize consistent variance for rookie scouting (only called for rookies)"""
        # Core attributes that need consistent variance
        attributes = ['speed', 'strength', 'awareness']

        # Position-specific attributes
        if self.position == "QB":
            attributes.extend(['throw_power', 'throw_accuracy'])
        elif self.position in ["RB", "WR", "TE"]:
            attributes.extend(['catching', 'route_running'])
            if self.position == "RB":
                attributes.extend(['carrying', 'elusiveness'])
        elif self.position == "OL":
            attributes.extend(['pass_blocking', 'run_blocking'])
        elif self.position in ["DL", "LB", "CB", "S"]:
            attributes.extend(['tackling', 'coverage'])
            if self.position in ["DL", "LB"]:
                attributes.append('pass_rush')
        elif self.position in ["K", "P"]:
            attributes.extend(['kicking_power', 'kicking_accuracy'])

        # Assign random variance for each attribute (will be consistent throughout rookie year)
        for attr in attributes:
            if hasattr(self, attr):
                # Speed and throw_power get smaller variance
                if attr in ['speed', 'throw_power']:
                    self.scouting_variance[attr] = random.randint(-5, 5)
                else:
                    self.scouting_variance[attr] = random.randint(-15, 15)

    def _initialize_draft_scouting(self):
        """Initialize scouting variance for draft prospects"""
        # Store base variance for draft display
        attributes = ['speed', 'strength', 'awareness']

        # Position-specific attributes
        if self.position == "QB":
            attributes.extend(['throw_power', 'throw_accuracy'])
        elif self.position in ["RB", "WR", "TE"]:
            attributes.extend(['catching', 'route_running'])
            if self.position == "RB":
                attributes.extend(['carrying', 'elusiveness'])
        elif self.position == "OL":
            attributes.extend(['pass_blocking', 'run_blocking'])
        elif self.position in ["DL", "LB", "CB", "S"]:
            attributes.extend(['tackling', 'coverage'])
            if self.position in ["DL", "LB"]:
                attributes.append('pass_rush')

        # Assign base variance (tier 0 - no scouting investment)
        for attr in attributes:
            if hasattr(self, attr):
                if attr in ['speed', 'throw_power']:
                    self.scouting_variance[attr] = random.randint(-5, 5)
                else:
                    self.scouting_variance[attr] = random.randint(-15, 15)

    def get_draft_rating(self, attribute_name, scout_points_invested=0):
        """Get scouted rating for draft prospects based on scout points invested"""
        if not hasattr(self, attribute_name):
            return None

        actual_value = getattr(self, attribute_name)
        base_variance = self.scouting_variance.get(attribute_name, 0)

        # Determine variance scaling based on scout points
        if scout_points_invested >= 3:
            # 3 points: ±1 speed/throw_power, ±5 other
            if attribute_name in ['speed', 'throw_power']:
                scale = 0.2  # 1/5
            else:
                scale = 0.33  # 5/15
        elif scout_points_invested >= 1:
            # 1 point: ±3 speed/throw_power, ±10 other
            if attribute_name in ['speed', 'throw_power']:
                scale = 0.6  # 3/5
            else:
                scale = 0.67  # 10/15
        else:
            # 0 points: ±5 speed/throw_power, ±15 other (full variance)
            scale = 1.0

        adjusted_variance = int(base_variance * scale)
        return max(50, min(99, actual_value + adjusted_variance))

    def get_scouted_rating(self, attribute_name, current_week=1):
        """Get the scouted rating for an attribute based on current week (rookies only)"""
        if not hasattr(self, attribute_name):
            return None

        actual_value = getattr(self, attribute_name)

        # Non-rookies always show actual ratings
        if not self.is_rookie:
            return actual_value

        # Get the stored variance for this attribute
        base_variance = self.scouting_variance.get(attribute_name, 0)

        # Determine accuracy based on week
        if current_week >= 15:
            # Week 15+: Show actual ratings
            return actual_value
        elif current_week >= 8:
            # Week 8-14: Reduce variance
            if attribute_name in ['speed', 'throw_power']:
                # Scale down from +/-5 to +/-3
                adjusted_variance = int(base_variance * 0.6)  # 3/5 = 0.6
            else:
                # Scale down from +/-15 to +/-10
                adjusted_variance = int(base_variance * 0.67)  # 10/15 = 0.67
            return max(50, min(99, actual_value + adjusted_variance))
        else:
            # Week 1-7: Full variance
            return max(50, min(99, actual_value + base_variance))

    def get_overall_potential(self):
        """Calculate overall potential as average of all attribute potentials"""
        potentials = []

        # Universal attributes
        if hasattr(self, 'speed_potential'):
            potentials.append(self.speed_potential)
        if hasattr(self, 'strength_potential'):
            potentials.append(self.strength_potential)
        if hasattr(self, 'awareness_potential'):
            potentials.append(self.awareness_potential)

        # Position-specific attributes
        if self.position == "QB":
            if hasattr(self, 'throw_power_potential'):
                potentials.append(self.throw_power_potential)
            if hasattr(self, 'throw_accuracy_potential'):
                potentials.append(self.throw_accuracy_potential)

        elif self.position in ["RB", "WR", "TE"]:
            if hasattr(self, 'catching_potential'):
                potentials.append(self.catching_potential)
            if hasattr(self, 'route_running_potential'):
                potentials.append(self.route_running_potential)
            if self.position == "RB":
                if hasattr(self, 'carrying_potential'):
                    potentials.append(self.carrying_potential)
                if hasattr(self, 'elusiveness_potential'):
                    potentials.append(self.elusiveness_potential)

        elif self.position == "OL":
            if hasattr(self, 'pass_blocking_potential'):
                potentials.append(self.pass_blocking_potential)
            if hasattr(self, 'run_blocking_potential'):
                potentials.append(self.run_blocking_potential)

        elif self.position in ["DL", "LB", "CB", "S"]:
            if hasattr(self, 'tackling_potential'):
                potentials.append(self.tackling_potential)
            if hasattr(self, 'coverage_potential'):
                potentials.append(self.coverage_potential)
            if self.position in ["DL", "LB"]:
                if hasattr(self, 'pass_rush_potential'):
                    potentials.append(self.pass_rush_potential)

        elif self.position in ["K", "P"]:
            if hasattr(self, 'kicking_power_potential'):
                potentials.append(self.kicking_power_potential)
            if hasattr(self, 'kicking_accuracy_potential'):
                potentials.append(self.kicking_accuracy_potential)

        # Return average potential
        if potentials:
            return int(sum(potentials) / len(potentials))
        return self.skill  # Fallback to skill if no potentials found

    def reset_stats(self):
        """Reset all stats to zero"""
        attrs = [
            "pass_attempts", "pass_completions", "pass_yards", "pass_td", "interceptions",
            "longest_pass", "sacks_taken", "rush_attempts", "rush_yards", "rush_td",
            "longest_rush", "fumbles", "rec_targets", "rec_catches", "rec_yards", "rec_td",
            "drops", "longest_rec", "tackles", "sacks", "qb_pressure", "interceptions_def",
            "forced_fumbles", "fumble_recoveries", "pass_deflections",
            "fg_attempts", "fg_made", "longest_fg", "xp_attempts", "xp_made",
            "punt_attempts", "punt_yards", "longest_punt", "inside_20"
        ]
        for attr in attrs:
            setattr(self, attr, 0)

    def progress(self):
        """Age player and adjust skill based on age"""
        if self.retired:
            return

        # Determine progression rate based on age
        if self.age <= 25:
            change = random.randint(0, 3)
            attr_progression = 0.6  # Young players improve faster
        elif self.age <= 29:
            change = random.randint(-1, 2)
            attr_progression = 0.4  # Prime players maintain/slowly improve
        else:
            change = random.randint(-3, 1)
            attr_progression = 0.1  # Older players decline or maintain

        self.skill = max(50, min(99, self.skill + change))

        # Progress each attribute toward its potential
        self._progress_attribute('speed', 'speed_potential', attr_progression)
        self._progress_attribute('strength', 'strength_potential', attr_progression)
        self._progress_attribute('awareness', 'awareness_potential', attr_progression)

        # Position-specific attribute progression
        if self.position == "QB":
            self._progress_attribute('throw_power', 'throw_power_potential', attr_progression)
            self._progress_attribute('throw_accuracy', 'throw_accuracy_potential', attr_progression)

        elif self.position in ["RB", "WR", "TE"]:
            self._progress_attribute('catching', 'catching_potential', attr_progression)
            self._progress_attribute('route_running', 'route_running_potential', attr_progression)

            if self.position == "RB":
                self._progress_attribute('carrying', 'carrying_potential', attr_progression)
                self._progress_attribute('elusiveness', 'elusiveness_potential', attr_progression)

        elif self.position == "OL":
            self._progress_attribute('pass_blocking', 'pass_blocking_potential', attr_progression)
            self._progress_attribute('run_blocking', 'run_blocking_potential', attr_progression)

        elif self.position in ["DL", "LB", "CB", "S"]:
            self._progress_attribute('tackling', 'tackling_potential', attr_progression)
            self._progress_attribute('coverage', 'coverage_potential', attr_progression)

            if self.position in ["DL", "LB"]:
                self._progress_attribute('pass_rush', 'pass_rush_potential', attr_progression)

        elif self.position in ["K", "P"]:
            self._progress_attribute('kicking_power', 'kicking_power_potential', attr_progression)
            self._progress_attribute('kicking_accuracy', 'kicking_accuracy_potential', attr_progression)

        self.age += 1
        self.years_played += 1

        # After first season, rookie status is cleared (ratings become accurate)
        if self.is_rookie and self.years_played >= 1:
            self.is_rookie = False
            self.scouting_variance = {}  # Clear variance as it's no longer needed

    def _progress_attribute(self, attr_name, potential_name, progression_rate):
        """Progress a single attribute toward its potential"""
        if not hasattr(self, attr_name) or not hasattr(self, potential_name):
            return

        current = getattr(self, attr_name)
        potential = getattr(self, potential_name)

        # Calculate how much room for growth
        gap = potential - current

        if gap > 0:
            # Improve toward potential (with some randomness)
            improvement = int(gap * progression_rate * random.uniform(0.3, 1.0))
            new_value = min(potential, current + improvement)
        else:
            # Already at/above potential, small chance of decline with age
            if self.age > 30 and random.random() < 0.3:
                new_value = max(50, current - random.randint(0, 2))
            else:
                new_value = current

        setattr(self, attr_name, new_value)

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
            "forced_fumbles", "fumble_recoveries", "pass_deflections",
            "fg_attempts", "fg_made", "xp_attempts", "xp_made",
            "punt_attempts", "punt_yards", "inside_20"
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
        if self.longest_fg > self.career_stats.get("longest_fg", 0):
            self.career_stats["longest_fg"] = self.longest_fg
        if self.longest_punt > self.career_stats.get("longest_punt", 0):
            self.career_stats["longest_punt"] = self.longest_punt
