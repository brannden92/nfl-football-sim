import random
from prettytable import PrettyTable

# ============================
# --- PLAYER CLASS ---
# ============================
class Player:
    def __init__(self, name, position, skill, age):
        self.name = name
        self.position = position
        self.skill = skill
        self.age = age
        
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
        self.longest_rec = 0

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
        self.timeouts = 3

# ============================
# --- GAME CLOCK ---
# ============================
class GameClock:
    def __init__(self):
        self.quarter = 1
        self.time_remaining = 15 * 60  # 15 minutes in seconds
        self.two_min_warning_shown = [False, False, False, False]  # Track per quarter
    
    def format_time(self):
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return f"Q{self.quarter} - {minutes}:{seconds:02d}"
    
    def run_time(self, seconds):
        self.time_remaining -= seconds
        
        # Check for 2-minute warning
        if self.time_remaining <= 120 and not self.two_min_warning_shown[self.quarter - 1]:
            self.two_min_warning_shown[self.quarter - 1] = True
            print(f"    ⏰ TWO MINUTE WARNING - Q{self.quarter}")
            return True  # Clock stops
        
        if self.time_remaining <= 0:
            if self.quarter < 4:
                self.quarter += 1
                self.time_remaining = 15 * 60
                print(f"\n{'='*60}")
                print(f"END OF QUARTER {self.quarter - 1}")
                print(f"{'='*60}\n")
            else:
                return False  # Game over
        return False
    
    def is_game_over(self):
        return self.quarter > 4 or (self.quarter == 4 and self.time_remaining <= 0)
    
    def is_half_over(self):
        return self.quarter == 3 and self.time_remaining == 15 * 60

# ============================
# --- CREATE ROSTER ---
# ============================
def create_roster(team_name):
    players = []
    
    # Create 1 QB
    qb = Player(f"{team_name} QB1", "QB", 80, 27)
    players.append(qb)
    
    # Create 2 RBs
    for i in range(2):
        rb = Player(f"{team_name} RB{i+1}", "RB", 75, 25)
        players.append(rb)
    
    # Create 4 receivers (2 WR, 2 TE)
    for i in range(2):
        wr = Player(f"{team_name} WR{i+1}", "WR", 78, 26)
        players.append(wr)
    for i in range(2):
        te = Player(f"{team_name} TE{i+1}", "TE", 76, 26)
        players.append(te)
    
    # Create 10 defensive players
    for i in range(10):
        defender = Player(f"{team_name} DEF{i+1}", "DL", 77, 26)
        players.append(defender)
    
    return players

# ============================
# --- SIMULATE PLAY ---
# ============================
def simulate_play(offense, defense, down, distance, yards_to_go, game_clock):
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
    
    clock_stops = False  # Will the clock stop after this play?
    time_elapsed = 0
    yards_gained = 0
    result = ""
    
    if play_type == "pass":
        qb.pass_attempts += 1
        
        # Randomly select target - 70% WR/TE, 30% RB
        if random.random() < 0.30:
            receiver = rb  # Pass to RB
            is_rb_target = True
        else:
            receiver = random.choice(offense.wr_starters + offense.te_starters)
            is_rb_target = False
        
        receiver.rec_targets += 1
        
        success_rate = 0.63 + (qb.skill - def_player.skill) / 200  # Base 63% completion
        
        # Check for sack OR QB scramble
        if random.random() < 0.08:
            # 60% sack, 40% scramble
            if random.random() < 0.60:
                # Sack
                yards_gained = -random.randint(3, 8)
                qb.sacks_taken += 1
                time_elapsed = random.randint(4, 8)
                result = f"SACK for {abs(yards_gained)} yards"
            else:
                # QB Scramble
                yards_gained = random.randint(2, 12)
                qb.rush_attempts += 1
                qb.rush_yards += yards_gained
                if yards_gained > qb.longest_rush:
                    qb.longest_rush = yards_gained
                time_elapsed = random.randint(4, 8)
                result = f"{qb.name} scrambles for {yards_gained} yards"
                
                # QB could fumble on scramble
                if random.random() < 0.02:
                    qb.fumbles += 1
                    time_elapsed = random.randint(6, 10)
                    clock_stops = True
                    result = f"{qb.name} scrambles - FUMBLE - Turnover"
                    return yards_gained, time_elapsed, clock_stops, result, True
        
        # Check for interception
        elif random.random() < 0.025:
            qb.interceptions += 1
            time_elapsed = random.randint(5, 12)
            clock_stops = True
            result = "INTERCEPTION - Turnover"
            return yards_gained, time_elapsed, clock_stops, result, True  # Turnover
        
        # Incomplete pass
        elif random.random() > success_rate:
            yards_gained = 0
            time_elapsed = random.randint(4, 8)
            clock_stops = True  # Clock stops on incomplete
            result = "Incomplete pass"
        
        # Completed pass
        else:
            # Check for big play (8% chance)
            if random.random() < 0.08:
                # Big play! 20-75 yards
                yards_gained = random.randint(20, 75)
            else:
                # Normal play - shorter for RBs
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
            
            # Check if player went out of bounds (stops clock)
            if random.random() < 0.25:
                clock_stops = True
                result = f"Complete to {receiver.name} for {yards_gained} yards (out of bounds)"
            else:
                result = f"Complete to {receiver.name} for {yards_gained} yards"
            
            time_elapsed = random.randint(6, 12)
    
    else:  # Run play
        rb.rush_attempts += 1
        
        # Check for big run (5% chance)
        if random.random() < 0.05:
            # Big run! 15-80 yards
            yards_gained = random.randint(15, 80)
        else:
            # Normal run - more likely to be short
            yards_gained = random.randint(-2, 10) + (rb.skill - def_player.skill) // 20
        
        rb.rush_yards += yards_gained
        
        if yards_gained > rb.longest_rush:
            rb.longest_rush = yards_gained
        
        time_elapsed = random.randint(3, 7)
        result = f"{rb.name} rush for {yards_gained} yards"
        
        # Check for fumble
        if random.random() < 0.015:
            rb.fumbles += 1
            time_elapsed = random.randint(6, 10)
            clock_stops = True
            result = "FUMBLE - Turnover"
            return yards_gained, time_elapsed, clock_stops, result, True  # Turnover
    
    # Check for touchdown
    if yards_to_go - yards_gained <= 0:
        if play_type == "pass":
            # Check if it was a QB scramble (qb has rush attempts this play)
            if result.startswith(qb.name + " scrambles"):
                qb.rush_td += 1
            else:
                qb.pass_td += 1
                receiver.rec_td += 1
        else:
            rb.rush_td += 1
        offense.score += 7
        result += " - TOUCHDOWN!"
        clock_stops = True
    
    return yards_gained, time_elapsed, clock_stops, result, False

# ============================
# --- SIMULATE DRIVE ---
# ============================
def simulate_drive(offense, defense, game_clock):
    """Simulate a complete drive"""
    # Random starting field position
    starting_position = random.randint(20, 40)
    yards_to_go = 100 - starting_position
    
    down = 1
    distance = 10
    plays_this_drive = 0
    drive_start_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60  # Total game time at start
    
    print(f"\n  {offense.name} drive starts at their {starting_position} yard line")
    print(f"  {game_clock.format_time()}")
    
    while not game_clock.is_game_over() and yards_to_go > 0:
        plays_this_drive += 1
        
        # Handle 4th down BEFORE simulating the play
        if down == 4:
            # Field goal attempt
            if yards_to_go <= 40 and random.random() < 0.75:
                fg_distance = yards_to_go + 17
                time_used = random.randint(10, 15)
                if random.random() < 0.80:
                    offense.score += 3
                    print(f"    4th & {distance}: {fg_distance}-yard FIELD GOAL GOOD! ({time_used}s)")
                    print(f"    SCORE! {offense.name} {offense.score}")
                else:
                    print(f"    4th & {distance}: {fg_distance}-yard field goal MISSED ({time_used}s)")
                
                game_clock.run_time(time_used)
                drive_end_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60
                time_of_possession = drive_start_time - drive_end_time
                minutes = time_of_possession // 60
                seconds = time_of_possession % 60
                print(f"    Drive ends. ({plays_this_drive} plays, {minutes}:{seconds:02d} TOP)")
                return
            
            # Go for it on short yardage
            elif distance <= 2 and random.random() < 0.30:
                print(f"    4th & {distance}: Going for it!")
                # Continue to simulate play below
            else:
                # Punt
                punt_distance = random.randint(35, 55)
                time_used = random.randint(10, 15)
                print(f"    4th & {distance}: {punt_distance}-yard PUNT ({time_used}s)")
                game_clock.run_time(time_used)
                drive_end_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60
                time_of_possession = drive_start_time - drive_end_time
                minutes = time_of_possession // 60
                seconds = time_of_possession % 60
                print(f"    Drive ends. ({plays_this_drive} plays, {minutes}:{seconds:02d} TOP)")
                return
        
        # Simulate the play
        yards_gained, time_elapsed, clock_stops, result, is_turnover = simulate_play(
            offense, defense, down, distance, yards_to_go, game_clock
        )
        
        print(f"    {down}{['st','nd','rd','th'][min(down-1,3)]} & {distance}: {result} ({time_elapsed}s)")
        
        # Handle turnovers
        if is_turnover:
            drive_end_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60
            time_of_possession = drive_start_time - drive_end_time
            minutes = time_of_possession // 60
            seconds = time_of_possession % 60
            print(f"    Drive ends. ({plays_this_drive} plays, {minutes}:{seconds:02d} TOP)")
            return
        
        # Update field position
        yards_to_go -= yards_gained
        distance -= yards_gained
        
        # Check for touchdown
        if yards_to_go <= 0:
            kickoff_time = random.randint(5, 20)
            drive_end_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60
            time_of_possession = drive_start_time - drive_end_time
            minutes = time_of_possession // 60
            seconds = time_of_possession % 60
            print(f"    SCORE! {offense.name} {offense.score} ({plays_this_drive} plays, {minutes}:{seconds:02d} TOP)")
            # Run clock for PAT/kickoff
            game_clock.run_time(kickoff_time)
            return
        
        # Update downs
        if distance <= 0:
            down = 1
            distance = 10
            print(f"    FIRST DOWN! {game_clock.format_time()}")
        else:
            down += 1
        
        # Run game clock (unless it stops)
        if not clock_stops:
            # Between plays: 25-40 seconds normally, 8-12 seconds in hurry-up
            if game_clock.quarter >= 2 and game_clock.time_remaining < 120:
                # Hurry-up offense in final 2 minutes
                time_between = random.randint(8, 12)
            else:
                time_between = random.randint(25, 40)
            game_clock.run_time(time_between)
        else:
            # Clock stopped, but some time still elapses
            game_clock.run_time(random.randint(0, 1))
        
        # Add the play time
        game_clock.run_time(time_elapsed)
        
        # Safety check
        if plays_this_drive > 20:
            drive_end_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60
            time_of_possession = drive_start_time - drive_end_time
            minutes = time_of_possession // 60
            seconds = time_of_possession % 60
            print(f"    Drive ends (safety limit). ({plays_this_drive} plays, {minutes}:{seconds:02d} TOP)")
            return
    
    drive_end_time = game_clock.time_remaining + (game_clock.quarter - 1) * 15 * 60
    time_of_possession = drive_start_time - drive_end_time
    minutes = time_of_possession // 60
    seconds = time_of_possession % 60
    print(f"    Drive ends (time expired). ({plays_this_drive} plays, {minutes}:{seconds:02d} TOP)")

# ============================
# --- SIMULATE GAME ---
# ============================
def simulate_game(team1, team2):
    print(f"\n{'='*60}")
    print(f"{team1.name} vs {team2.name}")
    print(f"{'='*60}\n")
    
    team1.score = 0
    team2.score = 0
    team1.timeouts = 3
    team2.timeouts = 3
    
    game_clock = GameClock()
    
    possession = random.choice([team1, team2])
    print(f"{possession.name} wins the coin toss and receives")
    
    total_drives = 0
    
    while not game_clock.is_game_over():
        # Simulate drive
        if possession == team1:
            simulate_drive(team1, team2, game_clock)
            possession = team2
        else:
            simulate_drive(team2, team1, game_clock)
            possession = team1
        
        total_drives += 1
        
        # Add time for kickoff
        if not game_clock.is_game_over():
            game_clock.run_time(random.randint(5, 10))
        
        # Reset timeouts at halftime
        if game_clock.is_half_over():
            team1.timeouts = 3
            team2.timeouts = 3
            print("\n" + "="*60)
            print("HALFTIME")
            print("="*60)
    
    print(f"\n{'='*60}")
    print(f"FINAL SCORE")
    print(f"{team1.name}: {team1.score}")
    print(f"{team2.name}: {team2.score}")
    print(f"{'='*60}\n")
    
    return team1, team2, total_drives

# ============================
# --- PRINT STATS ---
# ============================
def print_stats(team):
    print(f"\n=== {team.name} STATS ===\n")
    
    print("PASSING:")
    table = PrettyTable()
    table.field_names = ["Player", "Comp", "Att", "Comp%", "Yards", "TD", "INT", "Y/A", "Long", "Sacks"]
    for qb in team.qb_starters:
        comp_pct = (qb.pass_completions / qb.pass_attempts * 100) if qb.pass_attempts > 0 else 0
        ypa = qb.pass_yards / qb.pass_attempts if qb.pass_attempts > 0 else 0
        table.add_row([qb.name, qb.pass_completions, qb.pass_attempts, 
                      round(comp_pct, 1), qb.pass_yards, qb.pass_td, qb.interceptions,
                      round(ypa, 1), qb.longest_pass, qb.sacks_taken])
    print(table)
    
    print("\nRUSHING:")
    table = PrettyTable()
    table.field_names = ["Player", "Att", "Yards", "TD", "Y/A", "Long", "Fum"]
    # Include QB and RBs
    rushers = team.qb_starters + team.rb_starters
    rushers = [r for r in rushers if r.rush_attempts > 0]
    rushers.sort(key=lambda x: x.rush_yards, reverse=True)
    
    for rusher in rushers:
        ya = rusher.rush_yards / rusher.rush_attempts if rusher.rush_attempts > 0 else 0
        table.add_row([rusher.name, rusher.rush_attempts, rusher.rush_yards, rusher.rush_td,
                      round(ya, 1), rusher.longest_rush, rusher.fumbles])
    print(table)
    
    print("\nRECEIVING:")
    table = PrettyTable()
    table.field_names = ["Player", "Rec", "Targets", "Yards", "TD", "Y/R", "Long"]
    # Include WRs, TEs, and RBs
    receivers = team.wr_starters + team.te_starters + team.rb_starters
    receivers = [r for r in receivers if r.rec_targets > 0]
    receivers.sort(key=lambda x: x.rec_yards, reverse=True)
    
    for rec in receivers:
        yr = rec.rec_yards / rec.rec_catches if rec.rec_catches > 0 else 0
        table.add_row([rec.name, rec.rec_catches, rec.rec_targets, 
                      rec.rec_yards, rec.rec_td, round(yr, 1), rec.longest_rec])
    print(table)

# ============================
# --- MAIN TEST ---
# ============================
def main():
    print("NFL TIME-BASED GAME SIMULATOR\n")
    
    # Create two teams
    team1 = Team("Patriots")
    team1.players = create_roster("Patriots")
    team1.qb_starters = [p for p in team1.players if p.position == "QB"]
    team1.rb_starters = [p for p in team1.players if p.position == "RB"]
    team1.wr_starters = [p for p in team1.players if p.position == "WR"]
    team1.te_starters = [p for p in team1.players if p.position == "TE"]
    team1.defense_starters = [p for p in team1.players if p.position == "DL"]
    
    team2 = Team("Chiefs")
    team2.players = create_roster("Chiefs")
    team2.qb_starters = [p for p in team2.players if p.position == "QB"]
    team2.rb_starters = [p for p in team2.players if p.position == "RB"]
    team2.wr_starters = [p for p in team2.players if p.position == "WR"]
    team2.te_starters = [p for p in team2.players if p.position == "TE"]
    team2.defense_starters = [p for p in team2.players if p.position == "DL"]
    
    # Simulate game
    team1, team2, total_drives = simulate_game(team1, team2)
    
    # Print stats
    print_stats(team1)
    print_stats(team2)
    
    # Calculate total plays for each team
    team1_plays = (team1.qb_starters[0].pass_attempts + 
                   sum(rb.rush_attempts for rb in team1.rb_starters))
    team2_plays = (team2.qb_starters[0].pass_attempts + 
                   sum(rb.rush_attempts for rb in team2.rb_starters))
    
    print("\n" + "="*60)
    print("GAME SUMMARY")
    print("="*60)
    print(f"Total drives in game: {total_drives}")
    print(f"{team1.name} total plays: {team1_plays}")
    print(f"{team2.name} total plays: {team2_plays}")
    print("="*60)

if __name__ == "__main__":
    main()