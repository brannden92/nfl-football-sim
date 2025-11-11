"""
Game simulation logic for the NFL Football Simulation
"""
import random
from config import STAT_ATTRS


def get_down_distance_str(down, distance):
    """Format down and distance string for play-by-play"""
    down_names = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
    return f"{down_names.get(down, str(down))} & {distance}"


def simulate_play(offense, defense, down, distance, yards_to_go):
    """Simulate a single play and return results with play description"""
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
                play_description = f"{qb.name} sacked by {def_player.name} for {abs(yards_gained)} yard loss"
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
                    play_description = f"{qb.name} scrambles for {yards_gained} yards, FUMBLES! Recovered by {def_player.name}"
                    return yards_gained, time_elapsed, clock_stops, True, play_description  # Turnover
                else:
                    play_description = f"{qb.name} scrambles for {yards_gained} yards"

        # Check for interception
        elif random.random() < 0.025:
            qb.interceptions += 1
            def_player.interceptions_def += 1
            time_elapsed = random.randint(5, 12)
            clock_stops = True
            play_description = f"{qb.name} pass INTERCEPTED by {def_player.name}!"
            return yards_gained, time_elapsed, clock_stops, True, play_description  # Turnover

        # Incomplete pass
        elif random.random() > success_rate:
            yards_gained = 0
            time_elapsed = random.randint(4, 8)
            clock_stops = True

            # Check if it was a drop
            if random.random() < 0.15:
                receiver.drops += 1
                play_description = f"{qb.name} pass to {receiver.name} incomplete (DROPPED)"
            else:
                play_description = f"{qb.name} pass to {receiver.name} incomplete"

        # Completed pass
        else:
            # Check for big play (8% chance)
            is_big_play = random.random() < 0.08
            if is_big_play:
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

            # Build description
            if is_big_play:
                play_description = f"{qb.name} DEEP pass to {receiver.name} for {yards_gained} yards!"
            else:
                play_description = f"{qb.name} pass to {receiver.name} for {yards_gained} yards"

            # Check if player went out of bounds
            if random.random() < 0.25:
                clock_stops = True

            time_elapsed = random.randint(6, 12)

    else:  # Run play
        rb.rush_attempts += 1

        # Check for big run (5% chance)
        is_big_run = random.random() < 0.05
        if is_big_run:
            yards_gained = random.randint(15, 80)
        else:
            yards_gained = random.randint(-2, 10) + (rb.skill - def_player.skill) // 20

        rb.rush_yards += yards_gained

        if yards_gained > rb.longest_rush:
            rb.longest_rush = yards_gained

        time_elapsed = random.randint(3, 7)

        # Build description
        if is_big_run:
            play_description = f"{rb.name} BREAKS FREE for {yards_gained} yards!"
        elif yards_gained < 0:
            play_description = f"{rb.name} tackled by {def_player.name} for {abs(yards_gained)} yard loss"
        else:
            play_description = f"{rb.name} rushes for {yards_gained} yards"

        # Check for fumble
        if random.random() < 0.015:
            rb.fumbles += 1
            def_player.forced_fumbles += 1
            if random.random() < 0.5:
                def_player.fumble_recoveries += 1
                time_elapsed = random.randint(6, 10)
                clock_stops = True
                play_description = f"{rb.name} rushes for {yards_gained} yards, FUMBLES! Recovered by {def_player.name}"
                return yards_gained, time_elapsed, clock_stops, True, play_description  # Turnover
            else:
                play_description = f"{rb.name} rushes for {yards_gained} yards, FUMBLES but {offense.name} recovers!"

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
            play_description += " TOUCHDOWN!!!"
        else:
            rb.rush_td += 1
            play_description += " TOUCHDOWN!!!"
        offense.score += 7
        clock_stops = True

    return yards_gained, time_elapsed, clock_stops, False, play_description


def simulate_drive(offense, defense):
    """Simulate a full drive with multiple plays until TD, turnover, or punt"""
    qb = offense.qb_starters[0]
    rb = offense.rb_starters[0]

    # Random starting field position (20-40 yard line typically)
    starting_position = random.randint(20, 40)
    yards_to_go = 100 - starting_position  # Distance to end zone

    down = 1
    distance = 10
    plays = []  # Collect play descriptions

    while yards_to_go > 0:
        # Handle 4th down BEFORE simulating play
        if down == 4:
            # Field goal attempt
            if yards_to_go <= 40 and random.random() < 0.75:
                fg_distance = yards_to_go + 17
                if random.random() < 0.80:
                    offense.score += 3
                    plays.append(f"Field goal attempt from {fg_distance} yards - GOOD!")
                else:
                    plays.append(f"Field goal attempt from {fg_distance} yards - MISSED!")
                return plays

            # Go for it on short yardage
            elif distance <= 2 and random.random() < 0.30:
                pass  # Continue to simulate play
            else:
                # Punt
                plays.append(f"Punt by {offense.name}")
                return plays

        # Simulate the play
        yards_gained, time_elapsed, clock_stops, is_turnover, play_description = simulate_play(
            offense, defense, down, distance, yards_to_go
        )

        # Add play description with down and distance context
        plays.append(f"{get_down_distance_str(down, distance)}: {play_description}")

        # Handle turnovers
        if is_turnover:
            return plays

        # Update field position
        yards_to_go -= yards_gained
        distance -= yards_gained

        # Check for touchdown
        if yards_to_go <= 0:
            return plays

        # Update downs
        if distance <= 0:
            down = 1
            distance = 10
        else:
            down += 1

        # Safety check
        if down > 4:
            return plays

    return plays


def _snapshot_player_stats(players):
    """Take a snapshot of current player stats"""
    snap = {}
    for p in players:
        snap[p.name] = {attr: getattr(p, attr, 0) for attr in STAT_ATTRS}
    return snap


def _compute_delta_and_store(team, before_snap, after_players):
    """Compute the delta between before and after stats and store in team.last_game_stats"""
    deltas = {}
    for p in after_players:
        name = p.name
        before = before_snap.get(name, {attr: 0 for attr in STAT_ATTRS})
        delta = {}
        for attr in STAT_ATTRS:
            after_val = getattr(p, attr, 0)
            delta[attr] = after_val - before.get(attr, 0)
        deltas[name] = delta
    team.last_game_stats = deltas


def simulate_game(team1, team2, user_team=None):
    """Simulate a full game between two teams"""
    # Take snapshots BEFORE the game (season totals before)
    before_team1 = _snapshot_player_stats(team1.players)
    before_team2 = _snapshot_player_stats(team2.players)

    # Do NOT reset player season stats here — we want them to accumulate.
    team1.score = 0
    team2.score = 0

    # Collect play-by-play
    all_plays = []

    # Number of drives per team (simulates possessions)
    drives_per_team = random.randint(11, 13)

    for _ in range(drives_per_team):
        plays1 = simulate_drive(team1, team2)
        if plays1:
            all_plays.append(f"\n--- {team1.name} Drive ---")
            all_plays.extend(plays1)

        plays2 = simulate_drive(team2, team1)
        if plays2:
            all_plays.append(f"\n--- {team2.name} Drive ---")
            all_plays.extend(plays2)

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
    if user_team is None or user_team in [team1.name, team2.name]:
        print(f"{team1.name} {team1.score} - {team2.name} {team2.score}")

    return winner
