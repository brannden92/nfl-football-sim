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
            else:
                # QB Scramble
                yards_gained = random.randint(2, 12)
                qb.rush_attempts += 1
                qb.rush_yards += yards_gained
                if yards_gained > qb.longest_rush:
                    qb.longest_rush = yards_gained
                time_elapsed = random.randint(4, 8)
                
                # QB could fumble on scramble
                if random.random() < 0.02:
                    qb.fumbles += 1
                    time_elapsed = random.randint(6, 10)
                    clock_stops = True
                    return yards_gained, time_elapsed, clock_stops, True  # Turnover
        
        # Check for interception
        elif random.random() < 0.025:
            qb.interceptions += 1
            def_player.interceptions_def += 1
            time_elapsed = random.randint(5, 12)
            clock_stops = True
            return yards_gained, time_elapsed, clock_stops, True  # Turnover
        
        # Incomplete pass
        elif random.random() > success_rate:
            yards_gained = 0
            time_elapsed = random.randint(4, 8)
            clock_stops = True
            
            # Check if it was a drop
            if random.random() < 0.15:
                receiver.drops += 1
        
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
        
        time_elapsed = random.randint(3, 7)
        
        # Check for fumble
        if random.random() < 0.015:
            rb.fumbles += 1
            def_player.forced_fumbles += 1
            if random.random() < 0.5:
                def_player.fumble_recoveries += 1
                time_elapsed = random.randint(6, 10)
                clock_stops = True
                return yards_gained, time_elapsed, clock_stops, True  # Turnover
    
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
        else:
            rb.rush_td += 1
        offense.score += 7
        clock_stops = True
    
    return yards_gained, time_elapsed, clock_stops, False

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

        elif self.position in ["DL", "LB", "CB", "S"]:
            self.tackling = min(99, max(50, self.skill + variance))
            self.tackling_potential = min(99, self.tackling + random.randint(5, 15))

            self.coverage = min(99, max(50, self.skill + variance))
            self.coverage_potential = min(99, self.coverage + random.randint(5, 15))

            if self.position in ["DL", "LB"]:
                self.pass_rush = min(99, max(50, self.skill + variance))
                self.pass_rush_potential = min(99, self.pass_rush + random.randint(5, 15))

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
        elif self.position in ["DL", "LB", "CB", "S"]:
            attributes.extend(['tackling', 'coverage'])
            if self.position in ["DL", "LB"]:
                attributes.append('pass_rush')

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

    def reset_stats(self):
        attrs = ["pass_attempts","pass_completions","pass_yards","pass_td","interceptions",
                 "longest_pass","sacks_taken","rush_attempts","rush_yards","rush_td","longest_rush","fumbles",
                 "rec_targets","rec_catches","rec_yards","rec_td","drops","longest_rec",
                 "tackles","sacks","qb_pressure","interceptions_def","forced_fumbles","fumble_recoveries","pass_deflections"]
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

        elif self.position in ["DL", "LB", "CB", "S"]:
            self._progress_attribute('tackling', 'tackling_potential', attr_progression)
            self._progress_attribute('coverage', 'coverage_potential', attr_progression)

            if self.position in ["DL", "LB"]:
                self._progress_attribute('pass_rush', 'pass_rush_potential', attr_progression)

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
        "DL": 65,
        "LB": 60,
        "CB": 50,
        "S": 30
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
        print("4. Continue to Draft")
        choice = input("> ").strip()

        if choice == "1":
            # View prospects by position
            print("\nSelect Position:")
            positions = ["QB", "RB", "WR", "TE", "DL", "LB", "CB", "S", "ALL"]
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
            # View scouted players
            scouted = [(name, pts) for name, pts in franchise.scouting_investment.items()]
            if not scouted:
                print("\nNo players scouted yet.")
            else:
                print("\n=== Scouted Players ===")
                for name, pts in sorted(scouted, key=lambda x: x[1], reverse=True):
                    print(f"{name}: {pts} points")

        elif choice == "4":
            break

# ============================
# --- VIEW DRAFT PROSPECTS ---
# ============================
def view_draft_prospects(prospects, scouting_investment):
    """Display draft prospects with scouted ratings"""
    print(f"\n{'='*100}")
    print("DRAFT PROSPECTS".center(100))
    print(f"{'='*100}")

    table = PrettyTable()
    table.field_names = ["Name", "Pos", "Age", "Skill", "Speed", "Throw Pwr", "Catch", "Tackle", "Scout Pts"]

    for prospect in prospects:
        scout_pts = scouting_investment.get(prospect.name, 0)

        # Show different attributes based on position
        if prospect.position == "QB":
            attr1 = prospect.get_draft_rating('throw_power', scout_pts) or 'N/A'
            attr2 = prospect.get_draft_rating('throw_accuracy', scout_pts) or 'N/A'
            label = f"Pwr:{attr1}/Acc:{attr2}"
        elif prospect.position in ["RB", "WR", "TE"]:
            attr1 = prospect.get_draft_rating('catching', scout_pts) or 'N/A'
            label = f"{attr1}"
        else:  # Defense
            attr1 = prospect.get_draft_rating('tackling', scout_pts) or 'N/A'
            label = f"{attr1}"

        table.add_row([
            prospect.name,
            prospect.position,
            prospect.age,
            prospect.skill,
            prospect.get_draft_rating('speed', scout_pts) or 'N/A',
            attr1 if prospect.position == "QB" else "N/A",
            attr1 if prospect.position in ["RB", "WR", "TE"] else "N/A",
            attr1 if prospect.position in ["DL", "LB", "CB", "S"] else "N/A",
            f"★{scout_pts}" if scout_pts > 0 else "-"
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
        marker = " (YOU)" if team.name == franchise.user_team_name else ""
        print(f"{idx}. {team.name}{marker} ({team.wins}-{team.losses})")

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
    elif prospect.position in ["DL", "LB", "CB", "S"]:
        team.defense_starters.append(prospect)

    # Remove from available prospects
    available_prospects.remove(prospect)

    # Announce pick
    if show_details:
        print(f"\n✓ {team.name} selects {prospect.name} ({prospect.position}) - Round {round_num}, Pick {pick_num}")
    else:
        print(f"{team.name}: {prospect.name} ({prospect.position})")


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
    
    while yards_to_go > 0:
        # Handle 4th down BEFORE simulating play
        if down == 4:
            # Field goal attempt
            if yards_to_go <= 40 and random.random() < 0.75:
                fg_distance = yards_to_go + 17
                if random.random() < 0.80:
                    offense.score += 3
                return
            
            # Go for it on short yardage
            elif distance <= 2 and random.random() < 0.30:
                pass  # Continue to simulate play
            else:
                # Punt
                return
        
        # Simulate the play
        yards_gained, time_elapsed, clock_stops, is_turnover = simulate_play(
            offense, defense, down, distance, yards_to_go
        )
        
        # Handle turnovers
        if is_turnover:
            return
        
        # Update field position
        yards_to_go -= yards_gained
        distance -= yards_gained
        
        # Check for touchdown
        if yards_to_go <= 0:
            return
        
        # Update downs
        if distance <= 0:
            down = 1
            distance = 10
        else:
            down += 1
        
        # Safety check
        if down > 4:
            return

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

    # Number of drives per team (simulates possessions)
    drives_per_team = random.randint(11, 13)

    for _ in range(drives_per_team):
        simulate_drive(team1, team2)
        simulate_drive(team2, team1)

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

    # Print result only if user team involved (or no user specified)
    if user_team is None or user_team in [team1.name, team2.name]:
        print(f"{team1.name} {team1.score} - {team2.name} {team2.score}")

    return winner


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
    
    print(f"\n{'='*70}")
    print(f"{'YOUR TEAM: ' + team.name:^70}")
    print(f"{'='*70}")
    print(f"Record: {team.wins}-{team.losses} | {team.league} {team.division} | {div_rank}{get_ordinal(div_rank)} in Division")
    print(f"Points For: {team.points_for} (Rank: {offense_rank}{get_ordinal(offense_rank)})")
    print(f"Points Against: {team.points_against} (Rank: {defense_rank}{get_ordinal(defense_rank)})")
    print(f"Point Differential: {team.points_for - team.points_against:+d}")
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
                marker = " *" if team.name == user_team_name else ""
                table.add_row([
                    team.name + marker,
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

        print(f"\n=== SEASON {season_num} ===")
        print(f"Champion: {champion}")

        print("\nFinal Standings (Top 10):")
        table = PrettyTable()
        table.field_names = ["Rank", "Team", "W", "L", "PF", "PA", "Diff"]

        for rank, (name, wins, losses, pf, pa) in enumerate(season_result['standings'][:10], 1):
            marker = " 🏆" if name == champion else ""
            table.add_row([rank, name + marker, wins, losses, pf, pa, pf - pa])

        print(table)

# ============================
# --- VIEW PLAYER ATTRIBUTE PROGRESSION ---
# ============================
def view_player_progression(team, title="PLAYER ATTRIBUTE PROGRESSION", current_week=17):
    """Display player attributes and potentials (with scouting accuracy for rookies)"""
    print(f"\n{'='*80}")
    print(f"{title}: {team.name}".center(80))
    print(f"{'='*80}")

    # Group by position
    positions = {"QB": [], "RB": [], "WR": [], "TE": [], "DL": [], "LB": [], "CB": [], "S": []}

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
            table.field_names = ["Name", "Age", "Skill", "Speed", "Speed Pot", "Throw Pwr", "Pwr Pot", "Throw Acc", "Acc Pot"]
            for p in players_sorted:
                # Add rookie indicator if applicable
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    name_display, p.age, p.skill,
                    p.get_scouted_rating('speed', current_week) or 'N/A', getattr(p, 'speed_potential', 'N/A'),
                    p.get_scouted_rating('throw_power', current_week) or 'N/A', getattr(p, 'throw_power_potential', 'N/A'),
                    p.get_scouted_rating('throw_accuracy', current_week) or 'N/A', getattr(p, 'throw_accuracy_potential', 'N/A')
                ])

        elif position == "RB":
            table.field_names = ["Name", "Age", "Skill", "Speed", "Speed Pot", "Elusiveness", "Elusive Pot", "Carrying", "Carry Pot"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    name_display, p.age, p.skill,
                    p.get_scouted_rating('speed', current_week) or 'N/A', getattr(p, 'speed_potential', 'N/A'),
                    p.get_scouted_rating('elusiveness', current_week) or 'N/A', getattr(p, 'elusiveness_potential', 'N/A'),
                    p.get_scouted_rating('carrying', current_week) or 'N/A', getattr(p, 'carrying_potential', 'N/A')
                ])

        elif position in ["WR", "TE"]:
            table.field_names = ["Name", "Age", "Skill", "Speed", "Speed Pot", "Catching", "Catch Pot", "Route Run", "Route Pot"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    name_display, p.age, p.skill,
                    p.get_scouted_rating('speed', current_week) or 'N/A', getattr(p, 'speed_potential', 'N/A'),
                    p.get_scouted_rating('catching', current_week) or 'N/A', getattr(p, 'catching_potential', 'N/A'),
                    p.get_scouted_rating('route_running', current_week) or 'N/A', getattr(p, 'route_running_potential', 'N/A')
                ])

        elif position in ["DL", "LB", "CB", "S"]:
            table.field_names = ["Name", "Age", "Skill", "Speed", "Speed Pot", "Tackling", "Tackle Pot", "Coverage", "Cover Pot"]
            for p in players_sorted:
                name_display = p.name + (" (R)" if p.is_rookie else "")
                table.add_row([
                    name_display, p.age, p.skill,
                    p.get_scouted_rating('speed', current_week) or 'N/A', getattr(p, 'speed_potential', 'N/A'),
                    p.get_scouted_rating('tackling', current_week) or 'N/A', getattr(p, 'tackling_potential', 'N/A'),
                    p.get_scouted_rating('coverage', current_week) or 'N/A', getattr(p, 'coverage_potential', 'N/A')
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
        print(f"{i}. {team.name} ({team.wins}-{team.losses})")
    
    print("\n=== NFC PLAYOFF TEAMS ===")
    for i, team in enumerate(nfc_teams, 1):
        print(f"{i}. {team.name} ({team.wins}-{team.losses})")
    
    input("\nPress Enter to start Wild Card Round...")

    # Wild Card Round
    print("\n" + "="*70)
    print("WILD CARD ROUND".center(70))
    print("="*70)

    # Show teams with first-round BYE
    print("\n*** FIRST ROUND BYE ***")
    print(f"AFC: {afc_teams[0].name} ({afc_teams[0].wins}-{afc_teams[0].losses})")
    print(f"NFC: {nfc_teams[0].name} ({nfc_teams[0].wins}-{nfc_teams[0].losses})")

    afc_wc_winners = []
    nfc_wc_winners = []

    print("\n--- AFC Wild Card Games ---")
    # AFC Wild Card (2 vs 7, 3 vs 6, 4 vs 5)
    afc_wc_winners.append(simulate_game(afc_teams[1], afc_teams[6], user_team=None))
    afc_wc_winners.append(simulate_game(afc_teams[2], afc_teams[5], user_team=None))
    afc_wc_winners.append(simulate_game(afc_teams[3], afc_teams[4], user_team=None))

    print("\n--- NFC Wild Card Games ---")
    # NFC Wild Card
    nfc_wc_winners.append(simulate_game(nfc_teams[1], nfc_teams[6], user_team=None))
    nfc_wc_winners.append(simulate_game(nfc_teams[2], nfc_teams[5], user_team=None))
    nfc_wc_winners.append(simulate_game(nfc_teams[3], nfc_teams[4], user_team=None))
    
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
    afc_div_winners.append(simulate_game(afc_remaining[0], afc_remaining[3], user_team=None))
    afc_div_winners.append(simulate_game(afc_remaining[1], afc_remaining[2], user_team=None))

    print("\n--- NFC Divisional Games ---")
    nfc_div_winners.append(simulate_game(nfc_remaining[0], nfc_remaining[3], user_team=None))
    nfc_div_winners.append(simulate_game(nfc_remaining[1], nfc_remaining[2], user_team=None))
    
    input("\nPress Enter to continue to Conference Championships...")
    
    # Conference Championships
    print("\n" + "="*70)
    print("CONFERENCE CHAMPIONSHIPS".center(70))
    print("="*70)

    print("\n--- AFC Championship Game ---")
    afc_champ = simulate_game(afc_div_winners[0], afc_div_winners[1], user_team=None)

    print("\n--- NFC Championship Game ---")
    nfc_champ = simulate_game(nfc_div_winners[0], nfc_div_winners[1], user_team=None)

    input("\nPress Enter to continue to the SUPER BOWL...")

    # Super Bowl
    print("\n" + "="*70)
    print("SUPER BOWL".center(70))
    print("="*70 + "\n")

    champion = simulate_game(afc_champ, nfc_champ, user_team=None)
    
    print("\n" + "="*70)
    print(f"🏆 {champion.name} WIN THE SUPER BOWL! 🏆".center(70))
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

                # Backward compatibility: Add attribute potentials if they don't exist
                if not hasattr(player, 'speed'):
                    player._initialize_attributes_and_potentials()

                # Backward compatibility: Add rookie tracking if it doesn't exist
                if not hasattr(player, 'is_rookie'):
                    # Existing players are not rookies
                    player.is_rookie = False
                    player.scouting_variance = {}

        # Backward compatibility: Add draft-related attributes
        if not hasattr(franchise, 'scouting_points'):
            franchise.scouting_points = 100
        if not hasattr(franchise, 'draft_prospects'):
            franchise.draft_prospects = []
        if not hasattr(franchise, 'scouting_investment'):
            franchise.scouting_investment = {}

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
                team.defense_starters = [p for p in team.players if p.position in ["DL","LB","CB","S"]]
                team.league = league_name
                team.division = div_name
                leagues[league_name][div_name].append(team)
                idx += 1
    teams = [t for l in leagues.values() for d in l.values() for t in d]
    return teams

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

            print("1. Simulate Week")
            print("2. View Last Game's Stats")
            print("3. View Your Team Season Stats")
            print("4. View Your Team Career Stats")
            print("5. View Other Team Stats")
            print("6. View Standings")
            print("7. View Franchise History")
            print("8. Save Franchise")
            print("9. Quit")
            choice = input("> ").strip()

            if choice == "1":
                # Simulate all games for the week (shuffle / pairing)
                random.shuffle(franchise.teams)
                for i in range(0, len(franchise.teams), 2):
                    simulate_game(franchise.teams[i], franchise.teams[i+1], user_team=franchise.user_team_name)

                # Show user team summary after each week
                print_team_summary(user_team, franchise.teams)
                franchise.current_week += 1

            elif choice == "2":
                # Last game's stats (per-player deltas)
                print_last_game_stats(user_team)

            elif choice == "3":
                # Season totals (accumulated)
                games_played = franchise.current_week - 1
                print_team_stats(user_team, games_played)

            elif choice == "4":
                # Career stats
                print_career_stats(user_team)

            elif choice == "5":
                games_played = franchise.current_week - 1
                for idx, t in enumerate(franchise.teams):
                    print(f"{idx+1}. {t.name}")
                try:
                    sel = int(input("Select team: ")) - 1
                    if 0 <= sel < len(franchise.teams):
                        print_team_stats(franchise.teams[sel], games_played)
                except:
                    print("Invalid selection.")

            elif choice == "6":
                view_standings(franchise.teams, user_team_name=franchise.user_team_name)

            elif choice == "7":
                view_franchise_history(franchise)

            elif choice == "8":
                save_franchise(franchise)

            elif choice == "9":
                save_franchise(franchise)
                return

            else:
                print("Invalid choice.")

        
        # Season complete - run playoffs
        print(f"\n{'='*70}")
        print("REGULAR SEASON COMPLETE".center(70))
        print(f"{'='*70}")
        view_standings(franchise.teams, user_team_name=franchise.user_team_name)
        
        input("\nPress Enter to start the playoffs...")
        champion = run_playoffs(franchise)

        # Save season results to history
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