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
        if self.retired: return
        if self.age <= 25: change = random.randint(0,3)
        elif self.age <= 29: change = random.randint(-1,2)
        else: change = random.randint(-3,1)
        self.skill = max(50,min(99,self.skill+change))
        self.age += 1
        self.years_played += 1

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

        # Accumulate season stats to career stats BEFORE resetting
        for team in franchise.teams:
            for player in team.players:
                player.accumulate_to_career()
                player.progress()
                if player.should_retire() and not player.retired:
                    player.retired = True
                    retired_players.append(player)
                    print(f"{player.name} ({team.name}) has retired at age {player.age}")

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