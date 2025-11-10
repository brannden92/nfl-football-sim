import pandas as pd
import random
from prettytable import PrettyTable
import pickle 

# ============================
# --- GAME CLOCK ---
# ============================
class GameClock:
    def __init__(self):
        self.quarter = 1
        self.time_remaining = 15 * 60  # 15 minutes in seconds
        self.two_min_warning_shown = [False, False, False, False]
    
    def format_time(self):
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return f"Q{self.quarter} - {minutes}:{seconds:02d}"
    
    def run_time(self, seconds):
        self.time_remaining -= seconds
        
        # Check for 2-minute warning
        if self.time_remaining <= 120 and not self.two_min_warning_shown[self.quarter - 1]:
            self.two_min_warning_shown[self.quarter - 1] = True
            return True  # Clock stops
        
        if self.time_remaining <= 0:
            if self.quarter < 4:
                self.quarter += 1
                self.time_remaining = 15 * 60
            else:
                return False  # Game over
        return False
    
    def is_game_over(self):
        return self.quarter > 4 or (self.quarter == 4 and self.time_remaining <= 0)
    
    def is_half_over(self):
        return self.quarter == 3 and self.time_remaining == 15 * 60

# ============================
# --- SIMULATE PLAY ---
# ============================
def simulate_play(offense, defense, down, distance, yards_to_go):
    """Simulate a single play and return results"""
    qb = offense.qb_starters[0]
    rb = random.choice(offense.rb_starters)
    def_player = random.choice(defense.defense_starters)

    # Choose play type based on down and distance
    if down == 3 and distance > 7:
        play_type = random.choices(["pass", "run"], weights=[0.75, 0.25])[0]
    elif distance <= 3:
        play_type = random.choices(["pass", "run"], weights=[0.45, 0.55])[0]
    else:
        play_type = random.choices(["pass", "run"], weights=[0.6, 0.4])[0]

    clock_stops = False
    time_elapsed = 0
    yards_gained = 0
    play_description = ""
    
    if play_type == "pass":
        qb.pass_attempts += 1
        
        # Randomly select target - 70% WR/TE, 30% RB
        if random.random() < 0.30:
            receiver = rb
            is_rb_target = True
        else:
            receiver = random.choice(offense.wr_starters + offense.te_starters)
            is_rb_target = False
        
        receiver.rec_targets += 1
        
        success_rate = 0.63 + (qb.skill - def_player.skill) / 200
        
        # Check for sack OR QB scramble
        if random.random() < 0.08:
            if random.random() < 0.60:
                # Sack
                yards_gained = -random.randint(3, 8)
                qb.sacks_taken += 1
                time_elapsed = random.randint(4, 8)
                play_description = f"{qb.name} sacked by {def_player.name} for {yards_gained} yards"
            else:
                # QB Scramble
                yards_gained = random.randint(2, 12)
                qb.rush_attempts += 1
                qb.rush_yards += yards_gained
                if yards_gained > qb.longest_rush:
                    qb.longest_rush = yards_gained
                time_elapsed = random.randint(4, 8)
                play_description = f"{qb.name} scrambles for {yards_gained} yards"

                # QB could fumble on scramble
                if random.random() < 0.02:
                    qb.fumbles += 1
                    time_elapsed = random.randint(6, 10)
                    clock_stops = True
                    play_description = f"{qb.name} scrambles and fumbles! Recovered by {def_player.name}"
                    return yards_gained, time_elapsed, clock_stops, True, play_description  # Turnover
        
        # Check for interception
        elif random.random() < 0.025:
            qb.interceptions += 1
            def_player.interceptions_def += 1
            time_elapsed = random.randint(5, 12)
            clock_stops = True
            play_description = f"{qb.name} intercepted by {def_player.name}!"
            return yards_gained, time_elapsed, clock_stops, True, play_description  # Turnover

        # Incomplete pass
        elif random.random() > success_rate:
            yards_gained = 0
            time_elapsed = random.randint(4, 8)
            clock_stops = True

            # Check if it was a drop
            if random.random() < 0.15:
                receiver.drops += 1
                play_description = f"{qb.name} pass to {receiver.name} - DROPPED"
            else:
                play_description = f"{qb.name} pass to {receiver.name} incomplete"
        
        # Completed pass
        else:
            # Check for big play (8% chance)
            if random.random() < 0.08:
                yards_gained = random.randint(20, 75)
            else:
                if is_rb_target:
                    yards_gained = random.randint(1, 12) + (receiver.skill - def_player.skill) // 20
                else:
                    yards_gained = random.randint(3, 18) + (receiver.skill - def_player.skill) // 20

            qb.pass_completions += 1
            qb.pass_yards += yards_gained
            receiver.rec_catches += 1
            receiver.rec_yards += yards_gained

            if yards_gained > qb.longest_pass:
                qb.longest_pass = yards_gained
            if yards_gained > receiver.longest_rec:
                receiver.longest_rec = yards_gained

            play_description = f"{qb.name} pass to {receiver.name} for {yards_gained} yards"

            # Check if player went out of bounds
            if random.random() < 0.25:
                clock_stops = True

            time_elapsed = random.randint(6, 12)
    
    else:  # Run play
        rb.rush_attempts += 1

        # Check for big run (5% chance)
        if random.random() < 0.05:
            yards_gained = random.randint(15, 80)
        else:
            yards_gained = random.randint(-2, 10) + (rb.skill - def_player.skill) // 20

        rb.rush_yards += yards_gained

        if yards_gained > rb.longest_rush:
            rb.longest_rush = yards_gained

        play_description = f"{rb.name} rush for {yards_gained} yards"

        time_elapsed = random.randint(3, 7)

        # Check for fumble
        if random.random() < 0.015:
            rb.fumbles += 1
            def_player.forced_fumbles += 1
            if random.random() < 0.5:
                def_player.fumble_recoveries += 1
                time_elapsed = random.randint(6, 10)
                clock_stops = True
                play_description = f"{rb.name} fumbles! Recovered by {def_player.name}"
                return yards_gained, time_elapsed, clock_stops, True, play_description  # Turnover
    
    # Defensive stats
    def_player.tackles += 1
    if random.random() < 0.12:
        def_player.qb_pressure += 1
    if play_type == "pass" and random.random() < 0.08:
        def_player.pass_deflections += 1

    # Check for touchdown
    if yards_to_go - yards_gained <= 0:
        if play_type == "pass":
            qb.pass_td += 1
            receiver.rec_td += 1
            play_description += " - TOUCHDOWN!"
        else:
            rb.rush_td += 1
            play_description += " - TOUCHDOWN!"
        offense.score += 7
        clock_stops = True

    return yards_gained, time_elapsed, clock_stops, False, play_description

# ============================
# --- SIMULATE DRIVE ---
# ============================
# ============================
# --- IMPORTS ---
# ============================
import random
import pickle
import pandas as pd
from prettytable import PrettyTable

FRANCHISE_LENGTH = 40
SEASON_GAMES = 17

# ============================
# --- PLAYER CLASS ---
# ============================
class Player:
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

        # Season stats (current season only)
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

        # Kicker/Punter stats
        self.fg_attempts = 0
        self.fg_made = 0
        self.fg_longest = 0
        self.xp_attempts = 0
        self.xp_made = 0
        self.punts = 0
        self.punt_yards = 0
        self.punts_inside_20 = 0
        self.touchbacks = 0

        # Career stats (cumulative across all seasons)
        self.career_pass_attempts = 0
        self.career_pass_completions = 0
        self.career_pass_yards = 0
        self.career_pass_td = 0
        self.career_interceptions = 0
        self.career_sacks_taken = 0

        self.career_rush_attempts = 0
        self.career_rush_yards = 0
        self.career_rush_td = 0
        self.career_fumbles = 0

        self.career_rec_targets = 0
        self.career_rec_catches = 0
        self.career_rec_yards = 0
        self.career_rec_td = 0
        self.career_drops = 0

        self.career_tackles = 0
        self.career_sacks = 0
        self.career_qb_pressure = 0
        self.career_interceptions_def = 0
        self.career_forced_fumbles = 0
        self.career_fumble_recoveries = 0
        self.career_pass_deflections = 0

        self.career_fg_attempts = 0
        self.career_fg_made = 0
        self.career_fg_longest = 0
        self.career_xp_attempts = 0
        self.career_xp_made = 0
        self.career_punts = 0
        self.career_punt_yards = 0
        self.career_punts_inside_20 = 0
        self.career_touchbacks = 0

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

    def accumulate_to_career(self):
        """Add current season stats to career totals before resetting"""
        self.career_pass_attempts += self.pass_attempts
        self.career_pass_completions += self.pass_completions
        self.career_pass_yards += self.pass_yards
        self.career_pass_td += self.pass_td
        self.career_interceptions += self.interceptions
        self.career_sacks_taken += self.sacks_taken

        self.career_rush_attempts += self.rush_attempts
        self.career_rush_yards += self.rush_yards
        self.career_rush_td += self.rush_td
        self.career_fumbles += self.fumbles

        self.career_rec_targets += self.rec_targets
        self.career_rec_catches += self.rec_catches
        self.career_rec_yards += self.rec_yards
        self.career_rec_td += self.rec_td
        self.career_drops += self.drops

        self.career_tackles += self.tackles
        self.career_sacks += self.sacks
        self.career_qb_pressure += self.qb_pressure
        self.career_interceptions_def += self.interceptions_def
        self.career_forced_fumbles += self.forced_fumbles
        self.career_fumble_recoveries += self.fumble_recoveries
        self.career_pass_deflections += self.pass_deflections

        self.career_fg_attempts += self.fg_attempts
        self.career_fg_made += self.fg_made
        if self.fg_longest > self.career_fg_longest:
            self.career_fg_longest = self.fg_longest
        self.career_xp_attempts += self.xp_attempts
        self.career_xp_made += self.xp_made
        self.career_punts += self.punts
        self.career_punt_yards += self.punt_yards
        self.career_punts_inside_20 += self.punts_inside_20
        self.career_touchbacks += self.touchbacks

    def reset_stats(self):
        attrs = ["pass_attempts","pass_completions","pass_yards","pass_td","interceptions",
                 "longest_pass","sacks_taken","rush_attempts","rush_yards","rush_td","longest_rush","fumbles",
                 "rec_targets","rec_catches","rec_yards","rec_td","drops","longest_rec",
                 "tackles","sacks","qb_pressure","interceptions_def","forced_fumbles","fumble_recoveries","pass_deflections",
                 "fg_attempts","fg_made","fg_longest","xp_attempts","xp_made","punts","punt_yards","punts_inside_20","touchbacks"]
        for attr in attrs:
            setattr(self, attr, 0)

    def progress(self):
        """Progress player age and attributes based on potential"""
        if self.retired: return

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

    def should_retire(self):
        return self.age >= 35
    
# ============================
# --- TEAM CLASS ---
# ============================
class Team:
    def __init__(self, name):
        self.name = name
        self.players = []
        self.qb_starters = []
        self.rb_starters = []
        self.wr_starters = []
        self.te_starters = []
        self.ol_starters = []
        self.defense_starters = []
        self.k_starters = []
        self.p_starters = []
        self.score = 0
        self.wins = 0
        self.losses = 0
        self.points_for = 0
        self.points_against = 0
        self.league = None
        self.division = None
        self.last_game_stats = {}

    def reset_score(self):
        self.score = 0

    def reset_weekly_stats(self):
        for p in self.players:
            p.reset_stats()

# ============================
# --- FRANCHISE CLASS ---
# ============================
class Franchise:
    def __init__(self, teams, user_team_name, current_season=1, current_week=1):
        self.teams = teams
        self.user_team_name = user_team_name
        self.current_season = current_season
        self.current_week = current_week
        # Season history: list of dicts with season results
        if not hasattr(self, 'season_history'):
            self.season_history = []
        # Draft and scouting
        if not hasattr(self, 'scouting_points'):
            self.scouting_points = 100  # Starting scouting points
        if not hasattr(self, 'draft_prospects'):
            self.draft_prospects = []  # Will be populated before draft
        if not hasattr(self, 'scouting_investment'):
            self.scouting_investment = {}  # {player_name: points_spent}
        # Season schedule: list of weekly matchups [(team1, team2), ...]
        if not hasattr(self, 'season_schedule'):
            self.season_schedule = []  # Will be populated at season start
        # Game results: store all game results for the season
        if not hasattr(self, 'game_results'):
            self.game_results = []  # List of game result dictionaries

# ============================
# --- GENERATE SEASON SCHEDULE ---
# ============================
def generate_season_schedule(teams, num_weeks=17):
    """Generate a season schedule with balanced matchups and home/away designation"""
    import random

    schedule = []  # List of weeks, each week is list of (home_team, away_team) tuples
    teams_copy = teams.copy()

    for week in range(num_weeks):
        week_matchups = []
        random.shuffle(teams_copy)

        # Pair teams for this week (first team is home, second is away)
        for i in range(0, len(teams_copy), 2):
            # Randomly decide who's home/away
            if random.random() < 0.5:
                home_team = teams_copy[i]
                away_team = teams_copy[i+1]
            else:
                home_team = teams_copy[i+1]
                away_team = teams_copy[i]
            week_matchups.append((home_team, away_team))

        schedule.append(week_matchups)

    return schedule

def get_opponent(franchise, team_name):
    """Get the opponent for a team in the current week and whether it's home or away"""
    if not franchise.season_schedule or franchise.current_week > len(franchise.season_schedule):
        return None, None

    week_matchups = franchise.season_schedule[franchise.current_week - 1]

    for home_team, away_team in week_matchups:
        if home_team.name == team_name:
            return away_team, "home"  # This team is home
        elif away_team.name == team_name:
            return home_team, "away"  # This team is away

    return None, None

# ============================
# --- LOAD ROSTERS FROM EXCEL ---
# ============================
import pandas as pd

def load_rosters_from_excel(filename="fake_nfl_rosters.xlsx"):
    df = pd.read_excel(filename)
    df.columns = df.columns.str.strip()  # remove extra spaces

    teams = {}
    for _, row in df.iterrows():
        player = Player(
            name=row["Player Name"],
            position=row["Position"],
            skill=row["Skill"],
            age=row["Age"],
        )
        # Optional attributes
        player.durability = row.get("Durability", 100)
        player.starter_rank = row.get("Starter Rank", 1)

        team_name = row["Team"]
        if team_name not in teams:
            teams[team_name] = []
        teams[team_name].append(player)

    return teams  # dict: {team_name: [Player, Player, ...]}

# ============================
# --- GENERATE DRAFT PROSPECTS ---
# ============================
def generate_draft_prospects(num_prospects=350):
    """Generate rookies for the draft with varied skill levels"""
    prospects = []

    # Position distribution (roughly realistic)
    position_distribution = {
        "QB": 25,
        "RB": 35,
        "WR": 60,
        "TE": 25,
        "OL": 50,
        "DL": 65,
        "LB": 60,
        "CB": 50,
        "S": 30,
        "K": 5,
        "P": 5
    }

    # Generate players for each position
    prospect_id = 1
    for position, count in position_distribution.items():
        for i in range(count):
            # Skill distribution: more mid-tier players, fewer stars
            rand_val = random.random()
            if rand_val < 0.05:  # 5% elite prospects
                skill = random.randint(80, 92)
            elif rand_val < 0.20:  # 15% good prospects
                skill = random.randint(70, 79)
            elif rand_val < 0.60:  # 40% average prospects
                skill = random.randint(60, 69)
            else:  # 40% below average prospects
                skill = random.randint(50, 59)

            # Rookies are aged 21-22
            age = random.choice([21, 22])

            # Create prospect with descriptive name
            player_name = f"Draft {position}{prospect_id}"
            player = Player(player_name, position, skill, age)

            # Initialize scouting variance for draft display
            player._initialize_draft_scouting()

            prospects.append(player)
            prospect_id += 1

    # Shuffle to mix positions
    random.shuffle(prospects)
    return prospects

# ============================
# --- SCOUTING INTERFACE ---
# ============================
def run_scouting(franchise):
    """Allow user to invest scouting points in prospects"""
    print("\n" + "="*80)
    print(f"DRAFT SCOUTING - Available Points: {franchise.scouting_points}".center(80))
    print("="*80)
    print("\nScouting Investment Costs:")
    print("  - 1 point: Better accuracy (±3 speed/throw_power, ±10 other)")
    print("  - 3 points: High accuracy (±1 speed/throw_power, ±5 other)")
    print("  - Default: Base accuracy (±5 speed/throw_power, ±15 other)\n")

    while True:
        print(f"\nCurrent Scouting Points: {franchise.scouting_points}")
        print("\n1. View Prospects (by position)")
        print("2. Invest Scouting Points")
        print("3. View Scouted Players")
        print("4. Auto Scout (use remaining points)")
        print("5. Continue to Draft")
        choice = input("> ").strip()

        if choice == "1":
            # View prospects by position
            print("\nSelect Position:")
            positions = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S", "ALL"]
            for idx, pos in enumerate(positions, 1):
                print(f"{idx}. {pos}")

            try:
                pos_choice = int(input("> ")) - 1
                if 0 <= pos_choice < len(positions):
                    selected_pos = positions[pos_choice]
                    if selected_pos == "ALL":
                        prospects_to_show = franchise.draft_prospects[:50]  # Show first 50
                    else:
                        prospects_to_show = [p for p in franchise.draft_prospects if p.position == selected_pos][:30]

                    view_draft_prospects(prospects_to_show, franchise.scouting_investment)
            except:
                print("Invalid selection.")

        elif choice == "2":
            # Invest points
            print("\nEnter prospect name to scout (or 'back'):")
            name = input("> ").strip()
            if name.lower() == 'back':
                continue

            prospect = next((p for p in franchise.draft_prospects if p.name == name), None)
            if not prospect:
                print(f"Prospect '{name}' not found.")
                continue

            current_investment = franchise.scouting_investment.get(name, 0)
            print(f"\nCurrent investment in {name}: {current_investment} points")
            print("Invest 1 or 3 points? (or 0 to cancel)")
            try:
                investment = int(input("> "))
                if investment in [1, 3]:
                    new_total = current_investment + investment
                    if new_total > 3:
                        print("Cannot invest more than 3 points per player!")
                    elif franchise.scouting_points < investment:
                        print("Not enough scouting points!")
                    else:
                        franchise.scouting_points -= investment
                        franchise.scouting_investment[name] = new_total
                        print(f"Invested {investment} points. Total investment: {new_total}")
            except:
                print("Invalid investment amount.")

        elif choice == "3":
            # View scouted players with their ratings
            scouted = [(name, pts) for name, pts in franchise.scouting_investment.items()]
            if not scouted:
                print("\nNo players scouted yet.")
            else:
                print("\n=== Scouted Players ===")
                table = PrettyTable()
                table.field_names = ["Name", "Pos", "Age", "Skill", "Speed", "Strength", "Key Attr", "Scout Pts"]

                for name, pts in sorted(scouted, key=lambda x: x[1], reverse=True):
                    prospect = next((p for p in franchise.draft_prospects if p.name == name), None)
                    if prospect:
                        # Get scouted ratings based on investment
                        speed = prospect.get_draft_rating('speed', pts)
                        strength = prospect.get_draft_rating('strength', pts)

                        # Show position-specific key attribute
                        if prospect.position == "QB":
                            key_attr = f"Pwr:{prospect.get_draft_rating('throw_power', pts)}"
                        elif prospect.position in ["RB", "WR", "TE"]:
                            key_attr = f"Catch:{prospect.get_draft_rating('catching', pts)}"
                        elif prospect.position == "OL":
                            key_attr = f"Pass:{prospect.get_draft_rating('pass_blocking', pts)}"
                        elif prospect.position in ["K", "P"]:
                            key_attr = f"Kick:{prospect.get_draft_rating('kicking_accuracy', pts)}"
                        else:  # Defense
                            key_attr = f"Tack:{prospect.get_draft_rating('tackling', pts)}"

                        table.add_row([
                            prospect.name,
                            prospect.position,
                            prospect.age,
                            prospect.skill,
                            speed,
                            strength,
                            key_attr,
                            get_scout_indicator(pts)
                        ])

                print(table)

        elif choice == "4":
            # Auto scout - use remaining points on top prospects
            if franchise.scouting_points <= 0:
                print("\nNo scouting points remaining!")
                continue

            print(f"\nAuto-scouting will invest your remaining {franchise.scouting_points} points in top prospects.")
            print("Strategy: Invest 3 points in best players, then 1 point in next best.")
            confirm = input("Continue? (y/n): ").strip().lower()

            if confirm == 'y':
                # Sort all prospects by skill (best first)
                sorted_prospects = sorted(franchise.draft_prospects, key=lambda p: p.skill, reverse=True)

                scouted_count = 0
                for prospect in sorted_prospects:
                    if franchise.scouting_points <= 0:
                        break

                    current_investment = franchise.scouting_investment.get(prospect.name, 0)

                    # Skip if already fully scouted
                    if current_investment >= 3:
                        continue

                    # Try to invest 3 points if possible
                    if franchise.scouting_points >= 3 and current_investment == 0:
                        franchise.scouting_points -= 3
                        franchise.scouting_investment[prospect.name] = 3
                        scouted_count += 1
                    # Try to upgrade 1 point to 3 points
                    elif franchise.scouting_points >= 2 and current_investment == 1:
                        franchise.scouting_points -= 2
                        franchise.scouting_investment[prospect.name] = 3
                        scouted_count += 1
                    # Otherwise invest 1 point if possible
                    elif franchise.scouting_points >= 1 and current_investment == 0:
                        franchise.scouting_points -= 1
                        franchise.scouting_investment[prospect.name] = 1
                        scouted_count += 1

                print(f"\nAuto-scout complete! Scouted {scouted_count} prospects.")
                print(f"Remaining points: {franchise.scouting_points}")

        elif choice == "5":
            break

# ============================
# --- SCOUT INDICATOR HELPER ---
# ============================
def get_scout_indicator(scout_pts):
    """Return asterisk indicator based on scouting investment"""
    if scout_pts >= 3:
        return "**"  # 3 points = 2 asterisks
    elif scout_pts >= 1:
        return "*"   # 1 point = 1 asterisk
    else:
        return "-"   # No investment

# ============================
# --- VIEW DRAFT PROSPECTS ---
# ============================
def view_draft_prospects(prospects, scouting_investment):
    """Display draft prospects with scouted ratings"""
    print(f"\n{'='*110}")
    print("DRAFT PROSPECTS".center(110))
    print(f"{'='*110}")

    # Sort prospects by overall skill (highest to lowest)
    sorted_prospects = sorted(prospects, key=lambda p: p.skill, reverse=True)

    table = PrettyTable()
    table.field_names = ["Name", "Pos", "Age", "Skill", "Potential", "Speed", "Strength", "Key Attr", "Scout Pts"]

    for prospect in sorted_prospects:
        scout_pts = scouting_investment.get(prospect.name, 0)

        # Get overall potential
        overall_potential = prospect.get_overall_potential()

        # Show different attributes based on position
        if prospect.position == "QB":
            attr1 = prospect.get_draft_rating('throw_power', scout_pts) or 'N/A'
            key_attr = f"Pwr:{attr1}"
        elif prospect.position in ["RB", "WR", "TE"]:
            attr1 = prospect.get_draft_rating('catching', scout_pts) or 'N/A'
            key_attr = f"Catch:{attr1}"
        elif prospect.position == "OL":
            attr1 = prospect.get_draft_rating('pass_blocking', scout_pts) or 'N/A'
            key_attr = f"Pass:{attr1}"
        else:  # Defense
            attr1 = prospect.get_draft_rating('tackling', scout_pts) or 'N/A'
            key_attr = f"Tack:{attr1}"

        table.add_row([
            prospect.name,
            prospect.position,
            prospect.age,
            prospect.skill,
            overall_potential,
            prospect.get_draft_rating('speed', scout_pts) or 'N/A',
            prospect.get_draft_rating('strength', scout_pts) or 'N/A',
            key_attr,
            get_scout_indicator(scout_pts)
        ])

    print(table)

# ============================
# --- CALCULATE DRAFT ORDER ---
# ============================
def calculate_draft_order(franchise):
    """Calculate draft order based on inverse standings"""
    # Get all teams that didn't make playoffs first (worst to best record)
    playoff_teams_names = set()

    # Identify playoff teams (simplification: top 7 in each conference)
    afc_teams = sorted([t for t in franchise.teams if t.league == "AFC"],
                       key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)[:7]
    nfc_teams = sorted([t for t in franchise.teams if t.league == "NFC"],
                       key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)[:7]

    for t in afc_teams + nfc_teams:
        playoff_teams_names.add(t.name)

    # Non-playoff teams (pick 1-18)
    non_playoff = [t for t in franchise.teams if t.name not in playoff_teams_names]
    non_playoff_sorted = sorted(non_playoff,
                                key=lambda t: (t.wins, t.points_for - t.points_against))

    # Playoff teams (pick 19-32) - losers pick earlier
    playoff_sorted = sorted(afc_teams + nfc_teams,
                           key=lambda t: (t.wins, t.points_for - t.points_against))

    # Combine: non-playoff teams first, then playoff teams
    draft_order = non_playoff_sorted + playoff_sorted
    return draft_order

# ============================
# --- RUN NFL DRAFT ---
# ============================
def run_draft(franchise):
    """Conduct 7-round NFL draft"""
    print("\n" + "="*80)
    print("NFL DRAFT".center(80))
    print("="*80)

    draft_order = calculate_draft_order(franchise)
    available_prospects = franchise.draft_prospects.copy()
    ROUNDS = 7

    # Show draft order
    print("\n=== DRAFT ORDER ===")
    for idx, team in enumerate(draft_order, 1):
        emoji = get_team_emoji(team.name)
        marker = " (YOU)" if team.name == franchise.user_team_name else ""
        print(f"{idx}. {emoji} {team.name}{marker} ({team.wins}-{team.losses})")

    input("\nPress Enter to start the draft...")

    # Conduct draft
    for round_num in range(1, ROUNDS + 1):
        print(f"\n{'='*80}")
        print(f"ROUND {round_num}".center(80))
        print(f"{'='*80}")

        for pick_num, team in enumerate(draft_order, 1):
            overall_pick = (round_num - 1) * 32 + pick_num

            if not available_prospects:
                print("\nNo more prospects available!")
                return

            if team.name == franchise.user_team_name:
                # User's pick
                print(f"\n*** YOUR PICK - Round {round_num}, Pick {pick_num} (Overall #{overall_pick}) ***")
                print(f"Available Prospects: {len(available_prospects)}")

                while True:
                    print("\n1. View Available Prospects")
                    print("2. Make Selection")
                    print("3. Auto-pick (Best Available)")
                    choice = input("> ").strip()

                    if choice == "1":
                        # Show top prospects
                        print("\nTop 30 Available Prospects:")
                        view_draft_prospects(available_prospects[:30], franchise.scouting_investment)

                    elif choice == "2":
                        print("\nEnter prospect name to draft:")
                        name = input("> ").strip()
                        prospect = next((p for p in available_prospects if p.name == name), None)
                        if prospect:
                            draft_player(team, prospect, available_prospects, round_num, pick_num, overall_pick)
                            break
                        else:
                            print(f"Prospect '{name}' not found or already drafted.")

                    elif choice == "3":
                        # Auto-pick best available
                        prospect = available_prospects[0]
                        draft_player(team, prospect, available_prospects, round_num, pick_num, overall_pick)
                        break

            else:
                # CPU pick - simple best available
                prospect = available_prospects[0]
                draft_player(team, prospect, available_prospects, round_num, pick_num, overall_pick, show_details=False)

        input(f"\nRound {round_num} complete. Press Enter to continue...")

    print("\n" + "="*80)
    print("DRAFT COMPLETE!".center(80))
    print("="*80)

    # Reset scouting for next year
    franchise.scouting_points = 100
    franchise.scouting_investment = {}

def draft_player(team, prospect, available_prospects, round_num, pick_num, overall_pick, show_details=True):
    """Draft a player to a team"""
    # Add player to team
    team.players.append(prospect)

    # Update starter lists if applicable
    if prospect.position == "QB" and len(team.qb_starters) < 3:
        team.qb_starters.append(prospect)
    elif prospect.position == "RB" and len(team.rb_starters) < 5:
        team.rb_starters.append(prospect)
    elif prospect.position == "WR" and len(team.wr_starters) < 6:
        team.wr_starters.append(prospect)
    elif prospect.position == "TE" and len(team.te_starters) < 3:
        team.te_starters.append(prospect)
    elif prospect.position == "OL" and len(team.ol_starters) < 5:
        team.ol_starters.append(prospect)
    elif prospect.position == "K" and len(team.k_starters) < 1:
        team.k_starters.append(prospect)
    elif prospect.position == "P" and len(team.p_starters) < 1:
        team.p_starters.append(prospect)
    elif prospect.position in ["DL", "LB", "CB", "S"]:
        team.defense_starters.append(prospect)

    # Remove from available prospects
    available_prospects.remove(prospect)

    # Announce pick
    emoji = get_team_emoji(team.name)
    overall = prospect.skill
    potential = prospect.get_overall_potential()

    if show_details:
        print(f"\n✓ {emoji} {team.name} selects {prospect.name} ({prospect.position}) - OVR:{overall} POT:{potential} - Round {round_num}, Pick {pick_num}")
    else:
        print(f"{emoji} {team.name}: {prospect.name} ({prospect.position}) - OVR:{overall} POT:{potential}")


# ============================
# --- TEAM EMOJI HELPER ---
# ============================
def get_team_emoji(team_name):
    """Return an emoji that matches the team name"""
    emoji_map = {
        "Buffalo Bills": "🦬",
        "Miami Dolphins": "🐬",
        "New England Patriots": "🇺🇸",
        "New York Jets": "✈️",
        "Baltimore Ravens": "🐦",
        "Cincinnati Bengals": "🐅",
        "Cleveland Browns": "🟤",
        "Pittsburgh Steelers": "⚙️",
        "Houston Texans": "🤠",
        "Indianapolis Colts": "🐴",
        "Jacksonville Jaguars": "🐆",
        "Tennessee Titans": "⚡",
        "Denver Broncos": "🐴",
        "Kansas City Chiefs": "🏹",
        "Las Vegas Raiders": "🏴‍☠️",
        "Los Angeles Chargers": "⚡",
        "Dallas Cowboys": "⭐",
        "New York Giants": "🗽",
        "Philadelphia Eagles": "🦅",
        "Washington Commanders": "🎖️",
        "Chicago Bears": "🐻",
        "Detroit Lions": "🦁",
        "Green Bay Packers": "🧀",
        "Minnesota Vikings": "⚔️",
        "Atlanta Falcons": "🦅",
        "Carolina Panthers": "🐆",
        "New Orleans Saints": "⚜️",
        "Tampa Bay Buccaneers": "🏴‍☠️",
        "Arizona Cardinals": "🐦",
        "Los Angeles Rams": "🐏",
        "San Francisco 49ers": "⛏️",
        "Seattle Seahawks": "🦅"
    }
    return emoji_map.get(team_name, "🏈")

# ============================
# --- INJURY CHECK FUNCTION ---
# ============================
def check_injury(player):
    # Injuries are rare: 1 in 1000 chance per play * (100 - durability) factor
    chance = (100 - player.durability) / 100000
    if random.random() < chance:
        return True
    return False

# ============================
# --- SIMULATE DRIVE ---
# ============================
def simulate_drive(offense, defense):
    """Simulate a full drive with multiple plays until TD, turnover, or punt"""
    qb = offense.qb_starters[0]
    rb = offense.rb_starters[0]

    # Random starting field position (20-40 yard line typically)
    starting_position = random.randint(20, 40)
    yards_to_go = 100 - starting_position  # Distance to end zone

    down = 1
    distance = 10
    drive_plays = []

    while yards_to_go > 0:
        # Handle 4th down BEFORE simulating play
        if down == 4:
            # Field goal attempt
            if yards_to_go <= 40 and random.random() < 0.75:
                fg_distance = yards_to_go + 17
                kicker = offense.k_starters[0] if offense.k_starters else None
                if random.random() < 0.80:
                    offense.score += 3
                    if kicker:
                        play_desc = f"{kicker.name} {fg_distance}-yard field goal - GOOD!"
                    else:
                        play_desc = f"{fg_distance}-yard field goal - GOOD!"
                else:
                    if kicker:
                        play_desc = f"{kicker.name} {fg_distance}-yard field goal - MISSED"
                    else:
                        play_desc = f"{fg_distance}-yard field goal - MISSED"
                drive_plays.append(play_desc)
                return drive_plays

            # Go for it on short yardage
            elif distance <= 2 and random.random() < 0.30:
                pass  # Continue to simulate play
            else:
                # Punt
                punter = offense.p_starters[0] if offense.p_starters else None
                if punter:
                    play_desc = f"{punter.name} punts"
                else:
                    play_desc = "Punt"
                drive_plays.append(play_desc)
                return drive_plays

        # Simulate the play
        yards_gained, time_elapsed, clock_stops, is_turnover, play_description = simulate_play(
            offense, defense, down, distance, yards_to_go
        )

        # Add play description with down/distance context
        context = f"{down}{['st','nd','rd','th'][min(down-1,3)]} & {distance}"
        drive_plays.append(f"{context}: {play_description}")

        # Handle turnovers
        if is_turnover:
            return drive_plays

        # Update field position
        yards_to_go -= yards_gained
        distance -= yards_gained

        # Check for touchdown
        if yards_to_go <= 0:
            return drive_plays

        # Update downs
        if distance <= 0:
            down = 1
            distance = 10
        else:
            down += 1

        # Safety check
        if down > 4:
            return drive_plays

# ============================
# --- SIMULATE GAME ---
# ============================
STAT_ATTRS = [
    # Passing
    "pass_attempts","pass_completions","pass_yards","pass_td","interceptions","longest_pass","sacks_taken",
    # Rushing
    "rush_attempts","rush_yards","rush_td","longest_rush","fumbles",
    # Receiving
    "rec_targets","rec_catches","rec_yards","rec_td","drops","longest_rec",
    # Defense
    "tackles","sacks","qb_pressure","interceptions_def","forced_fumbles","fumble_recoveries","pass_deflections"
]

def _snapshot_player_stats(players):
    snap = {}
    for p in players:
        snap[p.name] = {attr: getattr(p, attr, 0) for attr in STAT_ATTRS}
    return snap

def _compute_delta_and_store(team, before_snap, after_players):
    deltas = {}
    for p in after_players:
        name = p.name
        before = before_snap.get(name, {attr:0 for attr in STAT_ATTRS})
        delta = {}
        for attr in STAT_ATTRS:
            after_val = getattr(p, attr, 0)
            delta[attr] = after_val - before.get(attr, 0)
        deltas[name] = delta
    team.last_game_stats = deltas

def simulate_game(team1, team2, user_team=None):
    # Take snapshots BEFORE the game (season totals before)
    before_team1 = _snapshot_player_stats(team1.players)
    before_team2 = _snapshot_player_stats(team2.players)

    # Do NOT reset player season stats here — we want them to accumulate.
    team1.score = 0
    team2.score = 0

    # Initialize play-by-play storage
    all_plays = []

    # Number of drives per team (simulates possessions)
    drives_per_team = random.randint(11, 13)

    for drive_num in range(drives_per_team):
        # Team 1 drive
        drive_plays = simulate_drive(team1, team2)
        if drive_plays:
            all_plays.append({
                'team': team1.name,
                'drive_num': (drive_num * 2) + 1,
                'plays': drive_plays
            })

        # Team 2 drive
        drive_plays = simulate_drive(team2, team1)
        if drive_plays:
            all_plays.append({
                'team': team2.name,
                'drive_num': (drive_num * 2) + 2,
                'plays': drive_plays
            })

    # Determine winner
    if team1.score > team2.score:
        winner = team1
    elif team2.score > team1.score:
        winner = team2
    else:
        # Overtime / tie-breaker
        winner = random.choice([team1, team2])
        winner.score += 3

    # Update team season aggregates
    team1.points_for += team1.score
    team1.points_against += team2.score
    team2.points_for += team2.score
    team2.points_against += team1.score

    if winner == team1:
        team1.wins += 1
        team2.losses += 1
    else:
        team2.wins += 1
        team1.losses += 1

    # Compute per-player deltas (last game's stats) and store on the team
    _compute_delta_and_store(team1, before_team1, team1.players)
    _compute_delta_and_store(team2, before_team2, team2.players)

    # Store play-by-play for both teams
    team1.last_game_plays = all_plays
    team2.last_game_plays = all_plays

    # Print result only if user team involved (or no user specified)
    emoji1 = get_team_emoji(team1.name)
    emoji2 = get_team_emoji(team2.name)
    if user_team is None or user_team in [team1.name, team2.name]:
        print(f"{emoji1} {team1.name} {team1.score} - {emoji2} {team2.name} {team2.score}")

    # Return game result information
    game_result = {
        'home_team': team1.name,
        'away_team': team2.name,
        'home_score': team1.score,
        'away_score': team2.score,
        'winner': winner.name,
        'plays': all_plays
    }

    return winner, game_result


# ============================
# --- GET TEAM SUMMARY ---
# ============================
def get_team_summary(team, all_teams):
    """Get team record, division standing, and league ranks"""
    # Get division teams
    div_teams = [t for t in all_teams if t.league == team.league and t.division == team.division]
    div_teams_sorted = sorted(div_teams, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    div_rank = div_teams_sorted.index(team) + 1
    
    # Get offensive rank (points scored)
    offense_sorted = sorted(all_teams, key=lambda t: t.points_for, reverse=True)
    offense_rank = offense_sorted.index(team) + 1
    
    # Get defensive rank (points allowed - lower is better)
    defense_sorted = sorted(all_teams, key=lambda t: t.points_against)
    defense_rank = defense_sorted.index(team) + 1
    
    return div_rank, offense_rank, defense_rank

def print_team_summary(team, all_teams):
    """Print summary of team's current season"""
    div_rank, offense_rank, defense_rank = get_team_summary(team, all_teams)

    emoji = get_team_emoji(team.name)
    point_diff = team.points_for - team.points_against

    print(f"\n{'='*70}")
    print(f"{'YOUR TEAM: ' + emoji + ' ' + team.name:^70}")
    print(f"{'='*70}")
    print(f"Record: {team.wins}-{team.losses} | {team.league} {team.division} | {div_rank}{get_ordinal(div_rank)} in Division")
    print(f"PF: {team.points_for} ({offense_rank}{get_ordinal(offense_rank)}) | PA: {team.points_against} ({defense_rank}{get_ordinal(defense_rank)}) | PD: {point_diff:+d}")
    print(f"{'='*70}\n")

def get_ordinal(n):
    """Return ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
    if 11 <= n % 100 <= 13:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')

# ============================
# --- VIEW TEAM STATS ---
# ============================
def print_team_stats(team, games_played):
    print(f"\n=== SEASON STATS (Through {games_played} Games) ===")
    
    print("\n=== Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Comp","Att","Comp%","Yards","TD","INT","Y/A","YPG","Long","Sacks"]
    qbs = sorted(team.qb_starters,key=lambda x:x.pass_yards,reverse=True)
    for qb in qbs:
        comp_pct = qb.pass_completions/qb.pass_attempts*100 if qb.pass_attempts else 0
        ypa = qb.pass_yards/qb.pass_attempts if qb.pass_attempts else 0
        ypg = qb.pass_yards/games_played if games_played > 0 else 0
        table.add_row([qb.name,qb.pass_completions,qb.pass_attempts,round(comp_pct,1),qb.pass_yards,
                       qb.pass_td,qb.interceptions,round(ypa,1),round(ypg,1),qb.longest_pass,qb.sacks_taken])
    print(table)

    print("\n=== Rushing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Att","Yards","TD","Y/A","YPG","Long","Fum"]
    # Include QBs and RBs
    rushers = team.qb_starters + team.rb_starters
    rushers = [r for r in rushers if r.rush_attempts > 0]
    rushers.sort(key=lambda x: x.rush_yards, reverse=True)
    rushers = rushers[:3]  # Top 3 rushers
    
    for rusher in rushers:
        ya = rusher.rush_yards/rusher.rush_attempts if rusher.rush_attempts else 0
        ypg = rusher.rush_yards/games_played if games_played > 0 else 0
        table.add_row([rusher.name,rusher.rush_attempts,rusher.rush_yards,rusher.rush_td,round(ya,1),round(ypg,1),rusher.longest_rush,rusher.fumbles])
    print(table)

    print("\n=== Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Rec","Targets","Yards","TD","Y/R","YPG","Long","Drops"]
    # Include RBs in receiving stats
    receivers = team.wr_starters + team.te_starters + team.rb_starters
    receivers = [r for r in receivers if r.rec_targets > 0]
    receivers.sort(key=lambda x: x.rec_yards, reverse=True)
    receivers = receivers[:6]  # Top 6 receivers
    
    for r in receivers:
        ypr = r.rec_yards/r.rec_catches if r.rec_catches else 0
        ypg = r.rec_yards/games_played if games_played > 0 else 0
        table.add_row([r.name,r.rec_catches,r.rec_targets,r.rec_yards,r.rec_td,round(ypr,1),round(ypg,1),r.longest_rec,r.drops])
    print(table)

    print("\n=== Defensive Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Tackles","Sacks","QB Pressure","INT","FF","FR","PD"]
    defenders = sorted(team.defense_starters,key=lambda x:(x.tackles+x.sacks),reverse=True)[:5]
    for d in defenders:
        table.add_row([d.name,d.tackles,d.sacks,d.qb_pressure,d.interceptions_def,d.forced_fumbles,d.fumble_recoveries,d.pass_deflections])
    print(table)

    # Kicking stats
    if team.k_starters:
        print("\n=== Kicking ===")
        table = PrettyTable()
        table.field_names = ["Name","FG","FGA","FG%","Long","XP","XPA","XP%"]
        for k in team.k_starters:
            fg_pct = k.fg_made/k.fg_attempts*100 if k.fg_attempts else 0
            xp_pct = k.xp_made/k.xp_attempts*100 if k.xp_attempts else 0
            table.add_row([k.name,k.fg_made,k.fg_attempts,round(fg_pct,1),k.fg_longest,k.xp_made,k.xp_attempts,round(xp_pct,1)])
        print(table)

    # Punting stats
    if team.p_starters:
        print("\n=== Punting ===")
        table = PrettyTable()
        table.field_names = ["Name","Punts","Yards","Y/P","In20","TB"]
        for p in team.p_starters:
            ypp = p.punt_yards/p.punts if p.punts else 0
            table.add_row([p.name,p.punts,p.punt_yards,round(ypp,1),p.punts_inside_20,p.touchbacks])
        print(table)

# ============================
# --- PRINT LAST GAME STATS ---
# ============================
def print_last_game_stats(team):
    """Print leaders/tables for the last game using team.last_game_stats (deltas)."""
    if not getattr(team, "last_game_stats", None):
        print("\nNo last game stats available for this team yet.")
        return

    lg = team.last_game_stats

    # Passing leaders (last game)
    print("\n=== LAST GAME: Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Player","Comp","Att","Yds","TD","INT","Comp%","Y/A","Long"]
    # find QBs present in last_game_stats
    qbs = [p for p in team.players if p.position=="QB"]
    for qb in qbs:
        d = lg.get(qb.name, {})
        att = d.get("pass_attempts", 0)
        comp = d.get("pass_completions", 0)
        yds = d.get("pass_yards", 0)
        td = d.get("pass_td", 0)
        itc = d.get("interceptions", 0)
        comp_pct = round(100 * comp / att, 1) if att else 0
        ypa = round(yds / att, 1) if att else 0
        table.add_row([qb.name, comp, att, yds, td, itc, comp_pct, ypa, d.get("longest_pass", 0)])
    print(table)

    # Rushing leaders (last game)
    print("\n=== LAST GAME: Rushing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Player","Att","Yds","TD","Y/A","Long"]
    rbs = [p for p in team.players if p.position=="RB"] + [p for p in team.players if p.position=="QB"]
    rbs_sorted = sorted(rbs, key=lambda x: lg.get(x.name, {}).get("rush_yards", 0), reverse=True)[:3]
    for r in rbs_sorted:
        d = lg.get(r.name, {})
        att = d.get("rush_attempts", 0)
        yds = d.get("rush_yards", 0)
        td = d.get("rush_td", 0)
        ya = round(yds/att,1) if att else 0
        table.add_row([r.name, att, yds, td, ya, d.get("longest_rush", 0)])
    print(table)

    # Receiving leaders (last game)
    print("\n=== LAST GAME: Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Player","Catches","Targets","Yds","TD","Y/R","Drops","Long"]
    recs = [p for p in team.players if p.position in ["WR","TE","RB"]]
    recs_sorted = sorted(recs, key=lambda x: lg.get(x.name, {}).get("rec_yards",0), reverse=True)[:6]
    for r in recs_sorted:
        d = lg.get(r.name, {})
        catches = d.get("rec_catches", 0)
        targets = d.get("rec_targets", 0)
        yds = d.get("rec_yards", 0)
        td = d.get("rec_td", 0)
        ypr = round(yds / catches, 1) if catches else 0
        table.add_row([r.name, catches, targets, yds, td, ypr, d.get("drops", 0), d.get("longest_rec", 0)])
    print(table)

    # Defensive leaders (last game)
    print("\n=== LAST GAME: Defensive Leaders ===")
    table = PrettyTable()
    table.field_names = ["Player","Tkl","Sacks","QB Press","INT","FF","FR","PD"]
    defs = team.defense_starters
    defs_sorted = sorted(defs, key=lambda x: lg.get(x.name, {}).get("tackles",0)+lg.get(x.name, {}).get("sacks",0), reverse=True)[:5]
    for d in defs_sorted:
        sd = lg.get(d.name, {})
        table.add_row([
            d.name,
            sd.get("tackles", 0),
            sd.get("sacks", 0),
            sd.get("qb_pressure", 0),
            sd.get("interceptions_def", 0),
            sd.get("forced_fumbles", 0),
            sd.get("fumble_recoveries", 0),
            sd.get("pass_deflections", 0)
        ])
    print(table)

# ============================
# --- VIEW LAST GAME PLAY-BY-PLAY ---
# ============================
def view_last_game_plays(team):
    """Display play-by-play for the last game"""
    if not hasattr(team, 'last_game_plays') or not team.last_game_plays:
        print("\nNo play-by-play data available for the last game.")
        return

    print(f"\n{'='*100}")
    print(f"LAST GAME PLAY-BY-PLAY".center(100))
    print(f"{'='*100}\n")

    for drive_info in team.last_game_plays:
        team_name = drive_info['team']
        drive_num = drive_info['drive_num']
        plays = drive_info['plays']

        emoji = get_team_emoji(team_name)
        print(f"\n--- DRIVE #{drive_num}: {emoji} {team_name} ---")
        for i, play in enumerate(plays, 1):
            print(f"  {i}. {play}")

    input("\nPress Enter to continue...")


# ============================
# --- VIEW STANDINGS ---
# ============================
def view_standings(teams, user_team_name=None):
    """Display league standings by division"""
    leagues = {"AFC": {"East": [], "North": [], "South": [], "West": []},
               "NFC": {"East": [], "North": [], "South": [], "West": []}}
    
    for team in teams:
        leagues[team.league][team.division].append(team)
    
    for league_name, divisions in leagues.items():
        print(f"\n{'='*60}")
        print(f"{league_name} STANDINGS")
        print(f"{'='*60}")
        
        for div_name, div_teams in divisions.items():
            sorted_teams = sorted(div_teams, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
            print(f"\n{league_name} {div_name}")
            print(f"{'-'*60}")
            
            table = PrettyTable()
            table.field_names = ["Team", "W", "L", "PF", "PA", "Diff"]
            
            for team in sorted_teams:
                emoji = get_team_emoji(team.name)
                marker = " *" if team.name == user_team_name else ""
                table.add_row([
                    emoji + " " + team.name + marker,
                    team.wins,
                    team.losses,
                    team.points_for,
                    team.points_against,
                    team.points_for - team.points_against
                ])
            
            print(table)

# ============================
# --- VIEW CAREER STATS ---
# ============================
def print_career_stats(team):
    """Print career stats for team players"""
    print(f"\n=== CAREER STATS: {team.name} ===")

    print("\n=== Career Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Seasons", "Comp", "Att", "Comp%", "Yards", "TD", "INT", "Y/A"]
    qbs = sorted([p for p in team.players if p.position == "QB" and p.career_pass_attempts > 0],
                 key=lambda x: x.career_pass_yards, reverse=True)[:5]
    for qb in qbs:
        comp_pct = qb.career_pass_completions / qb.career_pass_attempts * 100 if qb.career_pass_attempts else 0
        ypa = qb.career_pass_yards / qb.career_pass_attempts if qb.career_pass_attempts else 0
        table.add_row([qb.name, qb.years_played, qb.career_pass_completions, qb.career_pass_attempts,
                      round(comp_pct, 1), qb.career_pass_yards, qb.career_pass_td, qb.career_interceptions,
                      round(ypa, 1)])
    print(table)

    print("\n=== Career Rushing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Seasons", "Att", "Yards", "TD", "Y/A", "Fum"]
    rushers = sorted([p for p in team.players if p.career_rush_attempts > 0],
                     key=lambda x: x.career_rush_yards, reverse=True)[:5]
    for rb in rushers:
        ya = rb.career_rush_yards / rb.career_rush_attempts if rb.career_rush_attempts else 0
        table.add_row([rb.name, rb.years_played, rb.career_rush_attempts, rb.career_rush_yards,
                      rb.career_rush_td, round(ya, 1), rb.career_fumbles])
    print(table)

    print("\n=== Career Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Seasons", "Rec", "Targets", "Yards", "TD", "Y/R", "Drops"]
    receivers = sorted([p for p in team.players if p.career_rec_targets > 0],
                       key=lambda x: x.career_rec_yards, reverse=True)[:5]
    for r in receivers:
        ypr = r.career_rec_yards / r.career_rec_catches if r.career_rec_catches else 0
        table.add_row([r.name, r.years_played, r.career_rec_catches, r.career_rec_targets,
                      r.career_rec_yards, r.career_rec_td, round(ypr, 1), r.career_drops])
    print(table)

    print("\n=== Career Defensive Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Seasons", "Tackles", "Sacks", "QB Press", "INT", "FF", "FR", "PD"]
    defenders = sorted([p for p in team.players if p.position in ["DL", "LB", "CB", "S"]],
                       key=lambda x: (x.career_tackles + x.career_sacks), reverse=True)[:5]
    for d in defenders:
        table.add_row([d.name, d.years_played, d.career_tackles, d.career_sacks, d.career_qb_pressure,
                      d.career_interceptions_def, d.career_forced_fumbles, d.career_fumble_recoveries,
                      d.career_pass_deflections])
    print(table)

    # Career Kicking Stats
    kickers = [p for p in team.players if p.position == "K" and p.career_fg_attempts > 0]
    if kickers:
        print("\n=== Career Kicking Leaders ===")
        table = PrettyTable()
        table.field_names = ["Name", "Seasons", "FG", "FGA", "FG%", "Long", "XP", "XPA", "XP%"]
        kickers_sorted = sorted(kickers, key=lambda x: x.career_fg_made, reverse=True)
        for k in kickers_sorted:
            fg_pct = k.career_fg_made / k.career_fg_attempts * 100 if k.career_fg_attempts else 0
            xp_pct = k.career_xp_made / k.career_xp_attempts * 100 if k.career_xp_attempts else 0
            table.add_row([k.name, k.years_played, k.career_fg_made, k.career_fg_attempts,
                          round(fg_pct, 1), k.career_fg_longest, k.career_xp_made, k.career_xp_attempts,
                          round(xp_pct, 1)])
        print(table)

    # Career Punting Stats
    punters = [p for p in team.players if p.position == "P" and p.career_punts > 0]
    if punters:
        print("\n=== Career Punting Leaders ===")
        table = PrettyTable()
        table.field_names = ["Name", "Seasons", "Punts", "Yards", "Y/P", "In20", "TB"]
        punters_sorted = sorted(punters, key=lambda x: x.career_punts, reverse=True)
        for p in punters_sorted:
            ypp = p.career_punt_yards / p.career_punts if p.career_punts else 0
            table.add_row([p.name, p.years_played, p.career_punts, p.career_punt_yards,
                          round(ypp, 1), p.career_punts_inside_20, p.career_touchbacks])
        print(table)

# ============================
# --- VIEW FRANCHISE HISTORY ---
# ============================
def view_franchise_history(franchise):
    """Display historical season results"""
    if not franchise.season_history:
        print("\nNo franchise history available yet.")
        return

    print(f"\n{'='*70}")
    print("FRANCHISE HISTORY".center(70))
    print(f"{'='*70}")

    for season_result in franchise.season_history:
        season_num = season_result['season']
        champion = season_result['champion']

        champ_emoji = get_team_emoji(champion)
        print(f"\n=== SEASON {season_num} ===")
        print(f"Champion: {champ_emoji} {champion}")

        print("\nFinal Standings (Top 10):")
        table = PrettyTable()
        table.field_names = ["Rank", "Team", "W", "L", "PF", "PA", "Diff"]

        for rank, (name, wins, losses, pf, pa) in enumerate(season_result['standings'][:10], 1):
            emoji = get_team_emoji(name)
            marker = " 🏆" if name == champion else ""
            table.add_row([rank, emoji + " " + name + marker, wins, losses, pf, pa, pf - pa])

        print(table)

# ============================
# --- VIEW FULL ROSTER ---
# ============================
def view_full_roster(team, current_week=17):
    """Display full roster with ratings and depth chart positions"""
    print(f"\n{'='*100}")
    print(f"FULL ROSTER: {team.name}".center(100))
    print(f"{'='*100}")

    # Group by position
    positions = {"QB": [], "RB": [], "WR": [], "TE": [], "OL": [], "DL": [], "LB": [], "CB": [], "S": [], "K": [], "P": []}

    for player in team.players:
        if player.position in positions:
            positions[player.position].append(player)

    for position, players in positions.items():
        if not players:
            continue

        # Sort by skill to determine depth chart
        players_sorted = sorted(players, key=lambda p: p.skill, reverse=True)

        print(f"\n=== {position} ===")
        table = PrettyTable()

        # Determine columns based on position
        if position == "QB":
            table.field_names = ["Depth", "Name", "Age", "Skill", "Potential", "Speed", "Strength", "Throw Pwr", "Throw Acc"]
            for idx, p in enumerate(players_sorted, 1):
                depth = f"#{idx}"
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    depth, name_display, p.age, p.skill, p.get_overall_potential(),
                    p.get_scouted_rating('speed', current_week) or 'N/A',
                    p.get_scouted_rating('strength', current_week) or 'N/A',
                    p.get_scouted_rating('throw_power', current_week) or 'N/A',
                    p.get_scouted_rating('throw_accuracy', current_week) or 'N/A'
                ])

        elif position == "RB":
            table.field_names = ["Depth", "Name", "Age", "Skill", "Potential", "Speed", "Strength", "Elusiveness", "Carrying"]
            for idx, p in enumerate(players_sorted, 1):
                depth = f"#{idx}"
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    depth, name_display, p.age, p.skill, p.get_overall_potential(),
                    p.get_scouted_rating('speed', current_week) or 'N/A',
                    p.get_scouted_rating('strength', current_week) or 'N/A',
                    p.get_scouted_rating('elusiveness', current_week) or 'N/A',
                    p.get_scouted_rating('carrying', current_week) or 'N/A'
                ])

        elif position in ["WR", "TE"]:
            table.field_names = ["Depth", "Name", "Age", "Skill", "Potential", "Speed", "Strength", "Catching", "Route Run"]
            for idx, p in enumerate(players_sorted, 1):
                depth = f"#{idx}"
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    depth, name_display, p.age, p.skill, p.get_overall_potential(),
                    p.get_scouted_rating('speed', current_week) or 'N/A',
                    p.get_scouted_rating('strength', current_week) or 'N/A',
                    p.get_scouted_rating('catching', current_week) or 'N/A',
                    p.get_scouted_rating('route_running', current_week) or 'N/A'
                ])

        elif position == "OL":
            table.field_names = ["Depth", "Name", "Age", "Skill", "Potential", "Speed", "Strength", "Pass Block", "Run Block"]
            for idx, p in enumerate(players_sorted, 1):
                depth = f"#{idx}"
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    depth, name_display, p.age, p.skill, p.get_overall_potential(),
                    p.get_scouted_rating('speed', current_week) or 'N/A',
                    p.get_scouted_rating('strength', current_week) or 'N/A',
                    p.get_scouted_rating('pass_blocking', current_week) or 'N/A',
                    p.get_scouted_rating('run_blocking', current_week) or 'N/A'
                ])

        elif position in ["DL", "LB", "CB", "S"]:
            table.field_names = ["Depth", "Name", "Age", "Skill", "Potential", "Speed", "Strength", "Tackling", "Coverage"]
            for idx, p in enumerate(players_sorted, 1):
                depth = f"#{idx}"
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    depth, name_display, p.age, p.skill, p.get_overall_potential(),
                    p.get_scouted_rating('speed', current_week) or 'N/A',
                    p.get_scouted_rating('strength', current_week) or 'N/A',
                    p.get_scouted_rating('tackling', current_week) or 'N/A',
                    p.get_scouted_rating('coverage', current_week) or 'N/A'
                ])

        elif position in ["K", "P"]:
            table.field_names = ["Depth", "Name", "Age", "Skill", "Potential", "Speed", "Strength", "Kick Pwr", "Kick Acc"]
            for idx, p in enumerate(players_sorted, 1):
                depth = f"#{idx}"
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    depth, name_display, p.age, p.skill, p.get_overall_potential(),
                    p.get_scouted_rating('speed', current_week) or 'N/A',
                    p.get_scouted_rating('strength', current_week) or 'N/A',
                    p.get_scouted_rating('kicking_power', current_week) or 'N/A',
                    p.get_scouted_rating('kicking_accuracy', current_week) or 'N/A'
                ])

        print(table)

# ============================
# --- VIEW PLAYER ATTRIBUTE PROGRESSION ---
# ============================
def format_attr_with_change(current, prev_attr_name, player):
    """Format attribute value with change indicator"""
    if current == 'N/A':
        return 'N/A'

    prev = getattr(player, prev_attr_name, None)
    if prev is None:
        return str(current)

    change = current - prev
    if change > 0:
        return f"{current} (+{change})"
    elif change < 0:
        return f"{current} ({change})"
    else:
        return str(current)

def view_player_progression(team, title="PLAYER ATTRIBUTE PROGRESSION", current_week=17):
    """Display player attributes and potentials (with scouting accuracy for rookies)"""
    print(f"\n{'='*100}")
    print(f"{title}: {team.name}".center(100))
    print(f"{'='*100}")

    # Group by position
    positions = {"QB": [], "RB": [], "WR": [], "TE": [], "OL": [], "DL": [], "LB": [], "CB": [], "S": [], "K": [], "P": []}

    for player in team.players:
        if player.position in positions:
            positions[player.position].append(player)

    for position, players in positions.items():
        if not players:
            continue

        players_sorted = sorted(players, key=lambda p: p.skill, reverse=True)[:3]  # Top 3 per position

        print(f"\n=== {position} ===")
        table = PrettyTable()

        # Determine columns based on position
        if position == "QB":
            table.field_names = ["Name", "Age", "Skill", "Potential", "Speed", "Strength", "Throw Pwr", "Throw Acc"]
            for p in players_sorted:
                # Add rookie indicator if applicable
                name_display = p.name + (" (R)" if p.is_rookie else "")
                speed = p.get_scouted_rating('speed', current_week)
                strength = p.get_scouted_rating('strength', current_week)
                throw_power = p.get_scouted_rating('throw_power', current_week)
                throw_accuracy = p.get_scouted_rating('throw_accuracy', current_week)
                table.add_row([
                    name_display, p.age, p.skill, p.get_overall_potential(),
                    format_attr_with_change(speed, 'prev_speed', p),
                    format_attr_with_change(strength, 'prev_strength', p),
                    format_attr_with_change(throw_power, 'prev_throw_power', p),
                    format_attr_with_change(throw_accuracy, 'prev_throw_accuracy', p)
                ])

        elif position == "RB":
            table.field_names = ["Name", "Age", "Skill", "Potential", "Speed", "Strength", "Elusiveness", "Carrying"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                speed = p.get_scouted_rating('speed', current_week)
                strength = p.get_scouted_rating('strength', current_week)
                elusiveness = p.get_scouted_rating('elusiveness', current_week)
                carrying = p.get_scouted_rating('carrying', current_week)
                table.add_row([
                    name_display, p.age, p.skill, p.get_overall_potential(),
                    format_attr_with_change(speed, 'prev_speed', p),
                    format_attr_with_change(strength, 'prev_strength', p),
                    format_attr_with_change(elusiveness, 'prev_elusiveness', p),
                    format_attr_with_change(carrying, 'prev_carrying', p)
                ])

        elif position in ["WR", "TE"]:
            table.field_names = ["Name", "Age", "Skill", "Potential", "Speed", "Strength", "Catching", "Route Run"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                speed = p.get_scouted_rating('speed', current_week)
                strength = p.get_scouted_rating('strength', current_week)
                catching = p.get_scouted_rating('catching', current_week)
                route_running = p.get_scouted_rating('route_running', current_week)
                table.add_row([
                    name_display, p.age, p.skill, p.get_overall_potential(),
                    format_attr_with_change(speed, 'prev_speed', p),
                    format_attr_with_change(strength, 'prev_strength', p),
                    format_attr_with_change(catching, 'prev_catching', p),
                    format_attr_with_change(route_running, 'prev_route_running', p)
                ])

        elif position == "OL":
            table.field_names = ["Name", "Age", "Skill", "Potential", "Speed", "Strength", "Pass Block", "Run Block"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                speed = p.get_scouted_rating('speed', current_week)
                strength = p.get_scouted_rating('strength', current_week)
                pass_blocking = p.get_scouted_rating('pass_blocking', current_week)
                run_blocking = p.get_scouted_rating('run_blocking', current_week)
                table.add_row([
                    name_display, p.age, p.skill, p.get_overall_potential(),
                    format_attr_with_change(speed, 'prev_speed', p),
                    format_attr_with_change(strength, 'prev_strength', p),
                    format_attr_with_change(pass_blocking, 'prev_pass_blocking', p),
                    format_attr_with_change(run_blocking, 'prev_run_blocking', p)
                ])

        elif position in ["DL", "LB", "CB", "S"]:
            table.field_names = ["Name", "Age", "Skill", "Potential", "Speed", "Strength", "Tackling", "Coverage"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                speed = p.get_scouted_rating('speed', current_week)
                strength = p.get_scouted_rating('strength', current_week)
                tackling = p.get_scouted_rating('tackling', current_week)
                coverage = p.get_scouted_rating('coverage', current_week)
                table.add_row([
                    name_display, p.age, p.skill, p.get_overall_potential(),
                    format_attr_with_change(speed, 'prev_speed', p),
                    format_attr_with_change(strength, 'prev_strength', p),
                    format_attr_with_change(tackling, 'prev_tackling', p),
                    format_attr_with_change(coverage, 'prev_coverage', p)
                ])

        elif position in ["K", "P"]:
            table.field_names = ["Name", "Age", "Skill", "Potential", "Speed", "Strength", "Kick Pwr", "Kick Acc"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                speed = p.get_scouted_rating('speed', current_week)
                strength = p.get_scouted_rating('strength', current_week)
                kicking_power = p.get_scouted_rating('kicking_power', current_week)
                kicking_accuracy = p.get_scouted_rating('kicking_accuracy', current_week)
                table.add_row([
                    name_display, p.age, p.skill, p.get_overall_potential(),
                    format_attr_with_change(speed, 'prev_speed', p),
                    format_attr_with_change(strength, 'prev_strength', p),
                    format_attr_with_change(kicking_power, 'prev_kicking_power', p),
                    format_attr_with_change(kicking_accuracy, 'prev_kicking_accuracy', p)
                ])

        print(table)

# ============================
# --- PLAYOFFS ---
# ============================
def run_playoffs(franchise):
    """Run playoff bracket with division winners and wild cards"""
    print("\n" + "="*70)
    print("PLAYOFFS".center(70))
    print("="*70)
    
    # Get playoff teams for each conference
    afc_teams = get_playoff_teams([t for t in franchise.teams if t.league == "AFC"])
    nfc_teams = get_playoff_teams([t for t in franchise.teams if t.league == "NFC"])
    
    print("\n=== AFC PLAYOFF TEAMS ===")
    for i, team in enumerate(afc_teams, 1):
        emoji = get_team_emoji(team.name)
        print(f"{i}. {emoji} {team.name} ({team.wins}-{team.losses})")

    print("\n=== NFC PLAYOFF TEAMS ===")
    for i, team in enumerate(nfc_teams, 1):
        emoji = get_team_emoji(team.name)
        print(f"{i}. {emoji} {team.name} ({team.wins}-{team.losses})")
    
    input("\nPress Enter to start Wild Card Round...")

    # Wild Card Round
    print("\n" + "="*70)
    print("WILD CARD ROUND".center(70))
    print("="*70)

    # Show teams with first-round BYE
    print("\n*** FIRST ROUND BYE ***")
    afc_bye_emoji = get_team_emoji(afc_teams[0].name)
    nfc_bye_emoji = get_team_emoji(nfc_teams[0].name)
    print(f"AFC: {afc_bye_emoji} {afc_teams[0].name} ({afc_teams[0].wins}-{afc_teams[0].losses})")
    print(f"NFC: {nfc_bye_emoji} {nfc_teams[0].name} ({nfc_teams[0].wins}-{nfc_teams[0].losses})")

    afc_wc_winners = []
    nfc_wc_winners = []

    print("\n--- AFC Wild Card Games ---")
    # AFC Wild Card (2 vs 7, 3 vs 6, 4 vs 5)
    winner, _ = simulate_game(afc_teams[1], afc_teams[6], user_team=None)
    afc_wc_winners.append(winner)
    winner, _ = simulate_game(afc_teams[2], afc_teams[5], user_team=None)
    afc_wc_winners.append(winner)
    winner, _ = simulate_game(afc_teams[3], afc_teams[4], user_team=None)
    afc_wc_winners.append(winner)

    print("\n--- NFC Wild Card Games ---")
    # NFC Wild Card
    winner, _ = simulate_game(nfc_teams[1], nfc_teams[6], user_team=None)
    nfc_wc_winners.append(winner)
    winner, _ = simulate_game(nfc_teams[2], nfc_teams[5], user_team=None)
    nfc_wc_winners.append(winner)
    winner, _ = simulate_game(nfc_teams[3], nfc_teams[4], user_team=None)
    nfc_wc_winners.append(winner)
    
    input("\nPress Enter to continue to Divisional Round...")
    
    # Divisional Round
    print("\n" + "="*70)
    print("DIVISIONAL ROUND".center(70))
    print("="*70)

    # Re-seed winners (1 seed plays lowest remaining seed)
    afc_remaining = [afc_teams[0]] + sorted(afc_wc_winners, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    nfc_remaining = [nfc_teams[0]] + sorted(nfc_wc_winners, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)

    afc_div_winners = []
    nfc_div_winners = []

    print("\n--- AFC Divisional Games ---")
    winner, _ = simulate_game(afc_remaining[0], afc_remaining[3], user_team=None)
    afc_div_winners.append(winner)
    winner, _ = simulate_game(afc_remaining[1], afc_remaining[2], user_team=None)
    afc_div_winners.append(winner)

    print("\n--- NFC Divisional Games ---")
    winner, _ = simulate_game(nfc_remaining[0], nfc_remaining[3], user_team=None)
    nfc_div_winners.append(winner)
    winner, _ = simulate_game(nfc_remaining[1], nfc_remaining[2], user_team=None)
    nfc_div_winners.append(winner)
    
    input("\nPress Enter to continue to Conference Championships...")
    
    # Conference Championships
    print("\n" + "="*70)
    print("CONFERENCE CHAMPIONSHIPS".center(70))
    print("="*70)

    print("\n--- AFC Championship Game ---")
    afc_champ, _ = simulate_game(afc_div_winners[0], afc_div_winners[1], user_team=None)

    print("\n--- NFC Championship Game ---")
    nfc_champ, _ = simulate_game(nfc_div_winners[0], nfc_div_winners[1], user_team=None)

    input("\nPress Enter to continue to the SUPER BOWL...")

    # Super Bowl
    print("\n" + "="*70)
    print("SUPER BOWL".center(70))
    print("="*70 + "\n")

    champion, _ = simulate_game(afc_champ, nfc_champ, user_team=None)

    emoji = get_team_emoji(champion.name)
    print("\n" + "="*70)
    print(f"🏆 {emoji} {champion.name} WIN THE SUPER BOWL! 🏆".center(70))
    print("="*70)
    
    return champion

def get_playoff_teams(conference_teams):
    """Get 7 playoff teams from a conference (4 division winners + 3 wild cards)"""
    divisions = {}
    for team in conference_teams:
        if team.division not in divisions:
            divisions[team.division] = []
        divisions[team.division].append(team)
    
    # Get division winners
    div_winners = []
    for div_teams in divisions.values():
        winner = max(div_teams, key=lambda t: (t.wins, t.points_for - t.points_against))
        div_winners.append(winner)
    
    # Sort division winners by record
    div_winners.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    
    # Get wild card teams (best non-division winners)
    non_winners = [t for t in conference_teams if t not in div_winners]
    non_winners.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    wild_cards = non_winners[:3]
    
    # Return all 7 teams seeded by record
    playoff_teams = div_winners + wild_cards
    playoff_teams.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    
    return playoff_teams

# ============================
# --- SAVE / LOAD ---
# ============================
def save_franchise(franchise, filename="franchise_save.pkl"):
    with open(filename,"wb") as f:
        pickle.dump(franchise,f)
    print(f"Saved franchise to {filename}")

def load_franchise(filename="franchise_save.pkl"):
    try:
        with open(filename,"rb") as f:
            franchise = pickle.load(f)

        # Backward compatibility: Add season_history if it doesn't exist
        if not hasattr(franchise, 'season_history'):
            franchise.season_history = []

        # Backward compatibility: Add career stats to players if they don't exist
        for team in franchise.teams:
            for player in team.players:
                if not hasattr(player, 'career_pass_attempts'):
                    player.career_pass_attempts = 0
                    player.career_pass_completions = 0
                    player.career_pass_yards = 0
                    player.career_pass_td = 0
                    player.career_interceptions = 0
                    player.career_sacks_taken = 0
                    player.career_rush_attempts = 0
                    player.career_rush_yards = 0
                    player.career_rush_td = 0
                    player.career_fumbles = 0
                    player.career_rec_targets = 0
                    player.career_rec_catches = 0
                    player.career_rec_yards = 0
                    player.career_rec_td = 0
                    player.career_drops = 0
                    player.career_tackles = 0
                    player.career_sacks = 0
                    player.career_qb_pressure = 0
                    player.career_interceptions_def = 0
                    player.career_forced_fumbles = 0
                    player.career_fumble_recoveries = 0
                    player.career_pass_deflections = 0
                    player.career_fg_attempts = 0
                    player.career_fg_made = 0
                    player.career_fg_longest = 0
                    player.career_xp_attempts = 0
                    player.career_xp_made = 0
                    player.career_punts = 0
                    player.career_punt_yards = 0
                    player.career_punts_inside_20 = 0
                    player.career_touchbacks = 0

                # Backward compatibility: Add attribute potentials if they don't exist
                if not hasattr(player, 'speed'):
                    player._initialize_attributes_and_potentials()

                # Backward compatibility: Add rookie tracking if it doesn't exist
                if not hasattr(player, 'is_rookie'):
                    # Existing players are not rookies
                    player.is_rookie = False
                    player.scouting_variance = {}

            # Backward compatibility: Add k_starters and p_starters if they don't exist
            if not hasattr(team, 'k_starters'):
                team.k_starters = [p for p in team.players if p.position == "K"][:1]
            if not hasattr(team, 'p_starters'):
                team.p_starters = [p for p in team.players if p.position == "P"][:1]

            # Backward compatibility: Add last_game_plays if it doesn't exist
            if not hasattr(team, 'last_game_plays'):
                team.last_game_plays = []

        # Backward compatibility: Add draft-related attributes
        if not hasattr(franchise, 'scouting_points'):
            franchise.scouting_points = 100
        if not hasattr(franchise, 'draft_prospects'):
            franchise.draft_prospects = []
        if not hasattr(franchise, 'scouting_investment'):
            franchise.scouting_investment = {}

        # Backward compatibility: Add season schedule
        if not hasattr(franchise, 'season_schedule'):
            franchise.season_schedule = []

        # Backward compatibility: Add game results
        if not hasattr(franchise, 'game_results'):
            franchise.game_results = []

        print(f"Loaded franchise from {filename}")
        return franchise
    except:
        return None

# ============================
# --- CREATE NEW LEAGUE ---
# ============================
def create_new_league():
    # Load all rosters from Excel file
    rosters = load_rosters_from_excel("fake_nfl_rosters.xlsx")

    team_names = [
    "Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets",
    "Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans",
    "Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
    "Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders",
    "Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings",
    "Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers",
    "Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"
]

    leagues={"AFC":{"East":[],"North":[],"South":[],"West":[]},"NFC":{"East":[],"North":[],"South":[],"West":[]}}
    idx=0
    for league_name,divs in leagues.items():
        for div_name in divs:
            for _ in range(4):
                team = Team(team_names[idx])
                # Assign players from the rosters dictionary for this specific team
                team.players = rosters.get(team.name, [])
                team.qb_starters = [p for p in team.players if p.position=="QB"][:1]
                team.rb_starters = [p for p in team.players if p.position=="RB"][:2]
                team.wr_starters = [p for p in team.players if p.position=="WR"][:2]
                team.te_starters = [p for p in team.players if p.position=="TE"][:2]
                team.ol_starters = [p for p in team.players if p.position=="OL"][:5]
                team.defense_starters = [p for p in team.players if p.position in ["DL","LB","CB","S"]]
                team.k_starters = [p for p in team.players if p.position=="K"][:1]
                team.p_starters = [p for p in team.players if p.position=="P"][:1]
                team.league = league_name
                team.division = div_name
                leagues[league_name][div_name].append(team)
                idx += 1
    teams = [t for l in leagues.values() for d in l.values() for t in d]
    return teams

# ============================
# --- VIEW GAME RESULTS ---
# ============================
def view_game_results(franchise):
    """Display all game results for the current season"""
    if not franchise.game_results:
        print("\nNo games have been played yet this season.")
        return

    # Filter to current season
    current_season_games = [g for g in franchise.game_results if g.get('season', franchise.current_season) == franchise.current_season]

    if not current_season_games:
        print("\nNo games have been played yet this season.")
        return

    print(f"\n{'='*80}")
    print(f"GAME RESULTS - SEASON {franchise.current_season}".center(80))
    print(f"{'='*80}")

    # Group games by week
    weeks = {}
    for game in current_season_games:
        week = game['week']
        if week not in weeks:
            weeks[week] = []
        weeks[week].append(game)

    # Display games by week
    for week_num in sorted(weeks.keys()):
        print(f"\n{'='*80}")
        print(f"WEEK {week_num}".center(80))
        print(f"{'='*80}\n")

        for game in weeks[week_num]:
            home_emoji = get_team_emoji(game['home_team'])
            away_emoji = get_team_emoji(game['away_team'])
            home_score = game['home_score']
            away_score = game['away_score']

            # Mark winner with *
            if game['winner'] == game['home_team']:
                home_mark = "*"
                away_mark = ""
            else:
                home_mark = ""
                away_mark = "*"

            print(f"{away_emoji} {game['away_team']:25} @ {home_emoji} {game['home_team']:25}  {away_score:3}{away_mark} - {home_score:3}{home_mark}")

    input("\nPress Enter to continue...")

# ============================
# --- RUN FRANCHISE MENU ---
# ============================
def run_franchise(franchise):
    retired_players = []
    while franchise.current_season <= FRANCHISE_LENGTH:
        print(f"\n{'='*70}")
        print(f"SEASON {franchise.current_season}".center(70))
        print(f"{'='*70}")

        # Reset season records ONLY if starting a new season (week 1)
        # This prevents wiping stats when loading a saved game mid-season
        if franchise.current_week == 1:
            # Generate season schedule
            franchise.season_schedule = generate_season_schedule(franchise.teams, SEASON_GAMES)

            # Reset game results for new season
            franchise.game_results = []

            for t in franchise.teams:
                t.wins = 0
                t.losses = 0
                t.points_for = 0
                t.points_against = 0
                t.score = 0
                # Reset all player stats at start of season
                for p in t.players:
                    p.reset_stats()

        # Regular season
        while franchise.current_week <= SEASON_GAMES:
            print(f"\n{'='*70}")
            print(f"WEEK {franchise.current_week}".center(70))
            print(f"{'='*70}")

            user_team = next(t for t in franchise.teams if t.name == franchise.user_team_name)

            # Display opponent info
            opponent, home_away = get_opponent(franchise, franchise.user_team_name)
            if opponent:
                div_rank, offense_rank, defense_rank = get_team_summary(opponent, franchise.teams)

                # Show vs/@ notation
                user_emoji = get_team_emoji(user_team.name)
                opp_emoji = get_team_emoji(opponent.name)
                if home_away == "home":
                    matchup_str = f"{user_emoji} {user_team.name} vs {opp_emoji} {opponent.name}"
                else:
                    matchup_str = f"{user_emoji} {user_team.name} @ {opp_emoji} {opponent.name}"

                header = "THIS WEEK'S MATCHUP"
                print(f"\n{header:^70}")
                print(f"{'-'*70}")
                print(f"{matchup_str}")
                print(f"Record: {opponent.wins}-{opponent.losses} | {opponent.league} {opponent.division} | {div_rank}{get_ordinal(div_rank)} in Division")
                point_diff = opponent.points_for - opponent.points_against
                print(f"PF: {opponent.points_for} ({offense_rank}{get_ordinal(offense_rank)}) | PA: {opponent.points_against} ({defense_rank}{get_ordinal(defense_rank)}) | PD: {point_diff:+d}")
                print(f"{'-'*70}\n")

            print("1. Simulate Week")
            print("2. View Last Game's Stats")
            print("3. View Last Game's Play-by-Play")
            print("4. View Your Team Season Stats")
            print("5. View Your Team Career Stats")
            print("6. View Other Team Stats")
            print("7. View Standings")
            print("8. View Franchise History")
            print("9. View Full Roster")
            print("10. View Game Results")
            print("11. Save Franchise")
            print("12. Quit")
            choice = input("> ").strip()

            if choice == "1":
                # Simulate all games for the week using the scheduled matchups
                week_games = []
                if franchise.season_schedule and franchise.current_week <= len(franchise.season_schedule):
                    week_matchups = franchise.season_schedule[franchise.current_week - 1]
                    for home_team, away_team in week_matchups:
                        winner, game_result = simulate_game(home_team, away_team, user_team=franchise.user_team_name)
                        game_result['week'] = franchise.current_week
                        game_result['season'] = franchise.current_season
                        week_games.append(game_result)
                else:
                    # Fallback to random pairing if schedule not available
                    random.shuffle(franchise.teams)
                    for i in range(0, len(franchise.teams), 2):
                        winner, game_result = simulate_game(franchise.teams[i], franchise.teams[i+1], user_team=franchise.user_team_name)
                        game_result['week'] = franchise.current_week
                        game_result['season'] = franchise.current_season
                        week_games.append(game_result)

                # Store game results
                franchise.game_results.extend(week_games)

                # Show user team summary after each week
                print_team_summary(user_team, franchise.teams)
                franchise.current_week += 1

            elif choice == "2":
                # Last game's stats (per-player deltas)
                print_last_game_stats(user_team)

            elif choice == "3":
                # Last game's play-by-play
                view_last_game_plays(user_team)

            elif choice == "4":
                # Season totals (accumulated)
                games_played = franchise.current_week - 1
                print_team_stats(user_team, games_played)

            elif choice == "5":
                # Career stats
                print_career_stats(user_team)

            elif choice == "6":
                games_played = franchise.current_week - 1
                for idx, t in enumerate(franchise.teams):
                    emoji = get_team_emoji(t.name)
                    print(f"{idx+1}. {emoji} {t.name}")
                try:
                    sel = int(input("Select team: ")) - 1
                    if 0 <= sel < len(franchise.teams):
                        print_team_stats(franchise.teams[sel], games_played)
                except:
                    print("Invalid selection.")

            elif choice == "7":
                view_standings(franchise.teams, user_team_name=franchise.user_team_name)

            elif choice == "8":
                view_franchise_history(franchise)

            elif choice == "9":
                # View full roster with ratings
                view_full_roster(user_team, current_week=franchise.current_week)

            elif choice == "10":
                # View game results
                view_game_results(franchise)

            elif choice == "11":
                save_franchise(franchise)

            elif choice == "12":
                save_franchise(franchise)
                return

            else:
                print("Invalid choice.")


        # Season complete - run playoffs
        print(f"\n{'='*70}")
        print("REGULAR SEASON COMPLETE".center(70))
        print(f"{'='*70}")
        view_standings(franchise.teams, user_team_name=franchise.user_team_name)

        # Save regular season records BEFORE playoffs (for draft order)
        regular_season_records = {}
        for team in franchise.teams:
            regular_season_records[team.name] = {
                'wins': team.wins,
                'losses': team.losses,
                'points_for': team.points_for,
                'points_against': team.points_against
            }

        input("\nPress Enter to start the playoffs...")
        champion = run_playoffs(franchise)

        # Restore regular season records (playoff games don't count for standings/draft)
        for team in franchise.teams:
            if team.name in regular_season_records:
                record = regular_season_records[team.name]
                team.wins = record['wins']
                team.losses = record['losses']
                team.points_for = record['points_for']
                team.points_against = record['points_against']

        # Save season results to history (using regular season records)
        season_result = {
            'season': franchise.current_season,
            'champion': champion.name,
            'standings': [(t.name, t.wins, t.losses, t.points_for, t.points_against) for t in
                         sorted(franchise.teams, key=lambda x: (x.wins, x.points_for - x.points_against), reverse=True)]
        }
        franchise.season_history.append(season_result)

        # Progress players (aging, skill changes, retirements)
        print("\n=== OFF-SEASON ===")

        # ============================
        # NFL DRAFT
        # ============================
        print("\n--- DRAFT PREPARATION ---")
        franchise.draft_prospects = generate_draft_prospects(350)
        print(f"Generated {len(franchise.draft_prospects)} draft prospects")

        # Scouting phase
        print("\nEnter scouting phase to evaluate prospects...")
        input("Press Enter to begin scouting...")
        run_scouting(franchise)

        # Draft phase
        print("\nPreparing for the NFL Draft...")
        input("Press Enter to begin the draft...")
        run_draft(franchise)

        # Accumulate season stats to career stats BEFORE progression
        for team in franchise.teams:
            for player in team.players:
                # Save previous year's attributes before progression
                player.prev_speed = getattr(player, 'speed', player.skill)
                player.prev_strength = getattr(player, 'strength', player.skill)
                player.prev_awareness = getattr(player, 'awareness', player.skill)

                # Save position-specific attributes
                if player.position == "QB":
                    player.prev_throw_power = getattr(player, 'throw_power', player.skill)
                    player.prev_throw_accuracy = getattr(player, 'throw_accuracy', player.skill)
                elif player.position in ["RB", "WR", "TE"]:
                    player.prev_catching = getattr(player, 'catching', player.skill)
                    player.prev_route_running = getattr(player, 'route_running', player.skill)
                    if player.position == "RB":
                        player.prev_carrying = getattr(player, 'carrying', player.skill)
                        player.prev_elusiveness = getattr(player, 'elusiveness', player.skill)
                elif player.position == "OL":
                    player.prev_pass_blocking = getattr(player, 'pass_blocking', player.skill)
                    player.prev_run_blocking = getattr(player, 'run_blocking', player.skill)
                elif player.position in ["DL", "LB", "CB", "S"]:
                    player.prev_tackling = getattr(player, 'tackling', player.skill)
                    player.prev_coverage = getattr(player, 'coverage', player.skill)
                    if player.position in ["DL", "LB"]:
                        player.prev_pass_rush = getattr(player, 'pass_rush', player.skill)
                elif player.position in ["K", "P"]:
                    player.prev_kicking_power = getattr(player, 'kicking_power', player.skill)
                    player.prev_kicking_accuracy = getattr(player, 'kicking_accuracy', player.skill)

                player.accumulate_to_career()
                player.progress()
                if player.should_retire() and not player.retired:
                    player.retired = True
                    retired_players.append(player)
                    print(f"{player.name} ({team.name}) has retired at age {player.age}")

        # Show user team player progression
        user_team = next(t for t in franchise.teams if t.name == franchise.user_team_name)
        # Pass week 18 so all ratings are revealed after season ends
        view_player_progression(user_team, f"SEASON {franchise.current_season} PLAYER DEVELOPMENT", current_week=18)

        franchise.current_season += 1
        franchise.current_week = 1

        input("\nPress Enter to continue to next season...")
    
    print("\n" + "="*70)
    print("FRANCHISE COMPLETE!".center(70))
    print("="*70)

# ============================
# --- MAIN LOOP ---
# ============================
def main():
    print("=== NFL Franchise Simulator ===")
    print("1. New Game\n2. Load Game")
    choice = input("> ").strip()
    if choice == "2":
        franchise = load_franchise()
        if franchise is None:
            print("No save file found. Starting new game...")
            teams = create_new_league()
            for i, t in enumerate(teams): print(f"{i+1}. {t.name}")
            sel = int(input("Select your team: ")) - 1
            franchise = Franchise(teams, teams[sel].name)
    else:
        teams = create_new_league()
        for i, t in enumerate(teams): print(f"{i+1}. {t.name}")
        sel = int(input("Select your team: ")) - 1
        franchise = Franchise(teams, teams[sel].name)

    # Run your franchise menu here
    run_franchise(franchise)

    save_franchise(franchise)
    print("Franchise complete!")

if __name__=="__main__":
    main()