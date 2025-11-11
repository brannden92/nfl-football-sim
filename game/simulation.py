"""
Time-based game simulation logic for the NFL Football Simulation
"""
import random
from config import STAT_ATTRS


def get_down_distance_str(down, distance):
    """Format down and distance string for play-by-play"""
    down_names = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
    return f"{down_names.get(down, str(down))} & {distance}"


def get_field_position_str(team_abbrev, yard_line):
    """Convert yard line to field position string (e.g., 'DET 43')"""
    if yard_line == 50:
        return "50"
    elif yard_line > 50:
        return f"{team_abbrev} {100 - yard_line}"
    else:
        return f"OWN {yard_line}"


def get_team_abbrev(team_name):
    """Get 3-letter abbreviation for team"""
    words = team_name.split()
    if len(words) >= 2:
        return words[-1][:3].upper()
    return team_name[:3].upper()


def get_playcall_probabilities(down, distance, quarter, time_remaining, score_diff, field_pos):
    """Calculate run/pass probabilities based on game situation"""
    # Base probabilities from down and distance
    if down == 1:
        run, pas = 0.50, 0.50
    elif down == 2:
        if distance > 7:
            run, pas = 0.35, 0.65
        else:
            run, pas = 0.45, 0.55
    elif down == 3:
        if distance > 7:
            run, pas = 0.25, 0.75
        elif distance <= 3:
            run, pas = 0.50, 0.50
        else:
            run, pas = 0.35, 0.65
    else:  # 4th down (rarely used in this function)
        run, pas = 0.40, 0.60

    # Adjust for score/time in 4th quarter
    if quarter == 4:
        if score_diff < -7:  # Losing by more than a score
            run -= 0.20
            pas += 0.20
        elif score_diff < 0:  # Losing
            run -= 0.10
            pas += 0.10
        elif score_diff > 10:  # Winning big
            run += 0.25
            pas -= 0.25
        elif score_diff > 3:  # Winning
            run += 0.15
            pas -= 0.15

        # Clock management (last 2 minutes)
        if time_remaining < 120:
            if score_diff < 0:  # Losing, need to stop clock
                run -= 0.15
                pas += 0.15
            elif score_diff > 0:  # Winning, burn clock
                run += 0.20
                pas -= 0.20

    # Adjust for field position
    if field_pos < 20:  # Deep in own territory
        run += 0.10
        pas -= 0.10
    elif field_pos < 40:
        run += 0.05
        pas -= 0.05
    elif field_pos > 80:  # In red zone
        run += 0.15
        pas -= 0.15

    # Normalize (keep between 0–1)
    total = run + pas
    if total > 0:
        run /= total
        pas /= total

    return max(0.1, min(0.9, run)), max(0.1, min(0.9, pas))


def attempt_field_goal(kicker, distance):
    """Attempt a field goal with given kicker from given distance"""
    if not kicker:
        # No kicker, use default 80% from <40, 60% from 40-50, 40% from 50+
        if distance < 40:
            return random.random() < 0.80
        elif distance < 50:
            return random.random() < 0.60
        else:
            return random.random() < 0.40

    # Get kicker attributes
    kick_power = getattr(kicker, 'kicking_power', 75)
    kick_accuracy = getattr(kicker, 'kicking_accuracy', 75)

    # Base success rate from accuracy
    base_rate = kick_accuracy / 100

    # Adjust for distance
    if distance < 30:
        success_rate = base_rate * 0.98
    elif distance < 40:
        success_rate = base_rate * 0.92
    elif distance < 45:
        success_rate = base_rate * 0.85
    elif distance < 50:
        success_rate = base_rate * 0.75
    elif distance < 55:
        # Need good power to attempt from 50+
        if kick_power < 70:
            success_rate = 0.20
        else:
            success_rate = base_rate * 0.60
    else:
        if kick_power < 80:
            success_rate = 0.10
        else:
            success_rate = base_rate * 0.45

    return random.random() < success_rate


def attempt_punt(punter, distance_to_endzone):
    """Attempt a punt and return net yards and if it's a touchback"""
    if not punter:
        # Default punt: 35-50 yards
        punt_distance = random.randint(35, 50)
        is_touchback = punt_distance >= distance_to_endzone
        shanked = random.random() < 0.05
        if shanked:
            punt_distance = random.randint(15, 40)
        return punt_distance, is_touchback, shanked

    kick_power = getattr(punter, 'kicking_power', 70)
    kick_accuracy = getattr(punter, 'kicking_accuracy', 70)

    # Power determines distance
    base_distance = int(kick_power * 0.6)  # 70 power = ~42 yards
    punt_distance = base_distance + random.randint(-8, 12)

    # Check for shank (poor accuracy = more shanks)
    shank_chance = max(0.02, (100 - kick_accuracy) / 1000)
    shanked = random.random() < shank_chance
    if shanked:
        punt_distance = random.randint(15, 40)
        return punt_distance, False, True

    # Check if it would be a touchback
    is_touchback = punt_distance >= distance_to_endzone

    # If within 20 yards, accuracy determines if they pin it or get touchback
    if distance_to_endzone <= 20 and punt_distance >= distance_to_endzone:
        # Good accuracy = better chance to pin it
        pin_chance = kick_accuracy / 100 * 0.7
        if random.random() < pin_chance:
            # Successfully pinned inside 20
            is_touchback = False
            punt_distance = distance_to_endzone - random.randint(1, 10)

    return punt_distance, is_touchback, shanked


def simulate_play(offense, defense, down, distance, yards_to_go, quarter, time_remaining, score_diff, field_pos):
    """Simulate a single play and return results with play description"""
    if not offense.qb_starters or not offense.rb_starters:
        return 0, 20, False, False, "Error: Missing players"

    qb = offense.qb_starters[0]
    rb = random.choice(offense.rb_starters)
    def_player = random.choice(defense.defense_starters) if defense.defense_starters else None
    if not def_player:
        def_player = type('obj', (object,), {'skill': 65, 'name': 'Defender'})()

    # Calculate offensive line ratings
    ol_pass_blocking = 50
    ol_run_blocking = 50
    if offense.ol_starters:
        ol_pass_blocking = sum(getattr(ol, 'pass_blocking', ol.skill) for ol in offense.ol_starters) / len(offense.ol_starters)
        ol_run_blocking = sum(getattr(ol, 'run_blocking', ol.skill) for ol in offense.ol_starters) / len(offense.ol_starters)

    # Get play-calling probabilities
    run_prob, pass_prob = get_playcall_probabilities(down, distance, quarter, time_remaining, score_diff, field_pos)
    play_type = random.choices(["run", "pass"], weights=[run_prob, pass_prob])[0]

    clock_stops = False
    time_elapsed = 0
    yards_gained = 0
    play_description = ""

    if play_type == "pass":
        qb.pass_attempts += 1

        # Randomly select target
        if random.random() < 0.30 and offense.rb_starters:
            receiver = rb
            is_rb_target = True
        else:
            receivers = offense.wr_starters + offense.te_starters
            if not receivers:
                receivers = offense.rb_starters
            receiver = random.choice(receivers)
            is_rb_target = False

        receiver.rec_targets += 1

        # Pass blocking affects success rate and sack rate
        blocking_factor = (ol_pass_blocking - 70) / 400
        success_rate = 0.63 + (qb.skill - def_player.skill) / 200 + blocking_factor

        # Sack rate affected by pass blocking
        base_sack_rate = 0.08
        sack_modifier = (70 - ol_pass_blocking) / 1000
        sack_rate = max(0.02, min(0.15, base_sack_rate + sack_modifier))

        # Check for sack OR QB scramble
        if random.random() < sack_rate:
            if random.random() < 0.60:
                # Sack - pick a defensive lineman or linebacker
                sack_candidates = [p for p in defense.defense_starters if p.position in ['DL', 'LB']]
                if not sack_candidates:
                    sack_candidates = defense.defense_starters
                if sack_candidates:
                    sacker = random.choice(sack_candidates)
                    sacker.sacks += 1
                else:
                    sacker = def_player

                yards_gained = -random.randint(3, 8)
                qb.sacks_taken += 1
                time_elapsed = random.randint(4, 8)
                play_description = f"{qb.name} sacked by {sacker.name} for {abs(yards_gained)} yard loss"
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
                    return yards_gained, time_elapsed, clock_stops, True, play_description
                else:
                    play_description = f"{qb.name} scrambles for {yards_gained} yards"

        # Check for interception
        elif random.random() < 0.025:
            qb.interceptions += 1
            def_player.interceptions_def += 1
            time_elapsed = random.randint(5, 12)
            clock_stops = True
            play_description = f"{qb.name} pass INTERCEPTED by {def_player.name}!"
            return yards_gained, time_elapsed, clock_stops, True, play_description

        # Incomplete pass
        elif random.random() > success_rate:
            yards_gained = 0
            time_elapsed = random.randint(4, 8)
            clock_stops = True

            if random.random() < 0.15:
                receiver.drops += 1
                play_description = f"{qb.name} pass to {receiver.name} incomplete (DROPPED)"
            else:
                play_description = f"{qb.name} pass to {receiver.name} incomplete"

        # Completed pass
        else:
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

        # Run blocking affects yards gained
        blocking_bonus = int((ol_run_blocking - 70) / 10)
        big_run_chance = 0.05 + (ol_run_blocking - 70) / 1000
        is_big_run = random.random() < max(0.02, min(0.10, big_run_chance))

        if is_big_run:
            yards_gained = random.randint(15, 80)
        else:
            if ol_run_blocking < 60:
                base_yards = random.randint(-2, 8)
            elif ol_run_blocking < 70:
                base_yards = random.randint(-1, 9)
            elif ol_run_blocking > 80:
                base_yards = random.randint(0, 12)
            else:
                base_yards = random.randint(-2, 10)

            yards_gained = base_yards + (rb.skill - def_player.skill) // 20 + blocking_bonus

        rb.rush_yards += yards_gained

        if yards_gained > rb.longest_rush:
            rb.longest_rush = yards_gained

        time_elapsed = random.randint(3, 7)

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
                return yards_gained, time_elapsed, clock_stops, True, play_description
            else:
                play_description = f"{rb.name} rushes for {yards_gained} yards, FUMBLES but {offense.name} recovers!"

    # Defensive stats
    if def_player:
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
        offense.score += 6  # Touchdown is 6 points
        clock_stops = True

        # Extra point attempt (automatic - 99% success rate)
        kicker = offense.k_starters[0] if offense.k_starters else None
        if kicker:
            kicker.xp_attempts += 1
            if random.random() < 0.99:  # 99% XP success rate
                kicker.xp_made += 1
                offense.score += 1
        else:
            # No kicker, still convert at high rate
            if random.random() < 0.95:
                offense.score += 1

    return yards_gained, time_elapsed, clock_stops, False, play_description


def simulate_drive(offense, defense, start_field_pos, quarter, time_remaining, score_diff):
    """Simulate a full drive starting at given field position"""
    field_pos = start_field_pos  # 0-100 yard line
    yards_to_go = 100 - field_pos  # Distance to end zone
    down = 1
    distance = 10
    plays = []
    total_time_used = 0  # Track cumulative time used in this drive
    total_yards = 0  # Track yards gained on this drive

    off_abbrev = get_team_abbrev(offense.name)
    def_abbrev = get_team_abbrev(defense.name)

    # Add drive start info
    plays.append(f"\n--- {offense.name} starts at {get_field_position_str(def_abbrev, field_pos)} ---")

    while yards_to_go > 0 and time_remaining > 0:
        # Handle 4th down decisions
        if down == 4:
            distance_to_fg = yards_to_go + 17  # FG distance includes endzone

            # Field goal attempt
            if yards_to_go <= 45 and distance_to_fg <= 60:
                kicker = offense.k_starters[0] if offense.k_starters else None
                fg_made = attempt_field_goal(kicker, distance_to_fg)

                # Track kicker stats
                if kicker:
                    kicker.fg_attempts += 1
                    if fg_made:
                        kicker.fg_made += 1
                        if distance_to_fg > kicker.longest_fg:
                            kicker.longest_fg = distance_to_fg

                if fg_made:
                    offense.score += 3
                    play_time = 6
                    total_time_used += play_time
                    time_remaining -= play_time
                    mins, secs = divmod(int(time_remaining), 60)
                    kicker_name = kicker.name if kicker else "Kicker"
                    plays.append(f"Q{quarter} {mins}:{secs:02d} - 4th & {distance}: Field goal attempt from {distance_to_fg} yards by {kicker_name} - GOOD! ({play_time}s)")
                    return plays, 25, total_time_used, total_yards  # Touchback after FG
                else:
                    play_time = 5
                    total_time_used += play_time
                    time_remaining -= play_time
                    mins, secs = divmod(int(time_remaining), 60)
                    kicker_name = kicker.name if kicker else "Kicker"
                    plays.append(f"Q{quarter} {mins}:{secs:02d} - 4th & {distance}: Field goal attempt from {distance_to_fg} yards by {kicker_name} - MISSED! ({play_time}s)")
                    return plays, field_pos, total_time_used, total_yards  # Defense takes over

            # Go for it on short yardage near goal line
            elif distance <= 2 and yards_to_go <= 5:
                pass  # Continue to simulate play

            # Punt
            else:
                punter = offense.p_starters[0] if offense.p_starters else None
                punt_yards, is_touchback, shanked = attempt_punt(punter, yards_to_go)

                # Track punter stats
                if punter:
                    punter.punt_attempts += 1
                    punter.punt_yards += punt_yards
                    if punt_yards > punter.longest_punt:
                        punter.longest_punt = punt_yards
                    # Check if punt landed inside 20
                    if not is_touchback and not shanked:
                        new_field_pos_calc = field_pos + punt_yards
                        if new_field_pos_calc >= 80:  # Inside opponent 20
                            punter.inside_20 += 1

                play_time = 8
                total_time_used += play_time
                time_remaining -= play_time
                mins, secs = divmod(int(time_remaining), 60)

                punter_name = punter.name if punter else "Punter"
                if shanked:
                    new_field_pos = min(100, field_pos + punt_yards - 8)  # Return
                    plays.append(f"Q{quarter} {mins}:{secs:02d} - 4th & {distance}: {punter_name} SHANKED PUNT! {punt_yards} yards, returned to {get_field_position_str(off_abbrev, new_field_pos)} ({play_time}s)")
                elif is_touchback:
                    new_field_pos = 25
                    plays.append(f"Q{quarter} {mins}:{secs:02d} - 4th & {distance}: {punter_name} punts - touchback ({play_time}s)")
                else:
                    new_field_pos = field_pos + punt_yards - random.randint(0, 12)  # Return
                    new_field_pos = max(1, min(99, new_field_pos))
                    plays.append(f"Q{quarter} {mins}:{secs:02d} - 4th & {distance}: {punter_name} punts {punt_yards} yards to {get_field_position_str(off_abbrev, new_field_pos)} ({play_time}s)")

                return plays, new_field_pos, total_time_used, total_yards

        # Simulate the play
        yards_gained, play_time, clock_stops, is_turnover, play_description = simulate_play(
            offense, defense, down, distance, yards_to_go, quarter, time_remaining, score_diff, field_pos
        )

        # Calculate total time for this play (play time + time to next snap if clock runs)
        if clock_stops:
            # Clock stopped - only count play time
            time_for_play = play_time
        else:
            # Clock runs - add time between plays (huddle, lineup, snap)
            time_between_plays = random.randint(30, 40)
            time_for_play = play_time + time_between_plays

        # Update time
        total_time_used += time_for_play
        time_remaining -= time_for_play
        if time_remaining < 0:
            time_remaining = 0

        # Format time display
        mins, secs = divmod(int(time_remaining), 60)

        # Add play description with time info
        plays.append(f"Q{quarter} {mins}:{secs:02d} - {get_down_distance_str(down, distance)} at {get_field_position_str(def_abbrev, field_pos)}: {play_description} ({time_for_play}s)")

        # Track yards
        total_yards += yards_gained

        # Handle turnovers
        if is_turnover:
            return plays, field_pos + yards_gained, total_time_used, total_yards

        # Update field position
        field_pos += yards_gained
        yards_to_go -= yards_gained
        distance -= yards_gained

        # Check for safety (offense driven back into own endzone)
        if field_pos < 0:
            defense.score += 2
            plays.append(f"SAFETY! {defense.name} gets 2 points!")
            return plays, 20, total_time_used, total_yards  # Safety - offense kicks from their 20

        # Check for touchdown
        if yards_to_go <= 0:
            return plays, 25, total_time_used, total_yards  # Touchback after TD

        # Update downs
        if distance <= 0:
            down = 1
            distance = 10
        else:
            down += 1

        # Safety check
        if down > 4:
            return plays, field_pos, total_time_used, total_yards

    # Time ran out during drive
    return plays, field_pos, total_time_used, total_yards


def _snapshot_player_stats(players):
    """Take a snapshot of current player stats"""
    snap = {}
    for p in players:
        snap[p.name] = {attr: getattr(p, attr, 0) for attr in STAT_ATTRS}
    return snap


def _compute_delta_and_store(team, before_snap, after_players):
    """Compute the delta between before and after stats"""
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


def simulate_game(team1, team2, user_team=None, is_playoff=False):
    """Simulate a full game between two teams using time-based system

    Args:
        team1: First team
        team2: Second team
        user_team: User's team name (for display filtering)
        is_playoff: If True, updates playoff stats instead of regular season stats
    """
    # Take snapshots BEFORE the game
    before_team1 = _snapshot_player_stats(team1.players)
    before_team2 = _snapshot_player_stats(team2.players)

    team1.score = 0
    team2.score = 0

    all_plays = []

    # Track game stats
    team1_drives = 0
    team2_drives = 0
    team1_plays = 0
    team2_plays = 0
    team1_total_yards = 0
    team2_total_yards = 0

    # Game clock: 4 quarters x 15 minutes = 3600 seconds
    quarter = 1
    time_in_quarter = 900  # 15 minutes in seconds

    # Coin toss - team1 receives first
    possession = team1
    field_pos = 25  # Start at 25 yard line (touchback)

    while quarter <= 4:
        while time_in_quarter > 10:  # Need at least 10 seconds for a drive
            # Determine offense and defense
            if possession == team1:
                offense, defense = team1, team2
                team1_drives += 1
            else:
                offense, defense = team2, team1
                team2_drives += 1

            score_diff = offense.score - defense.score
            score_before = offense.score

            # Simulate drive
            drive_plays, end_field_pos, time_used, yards_gained = simulate_drive(
                offense, defense, field_pos, quarter, time_in_quarter, score_diff
            )

            # Count plays (subtract 1 for the drive header line)
            num_plays = len(drive_plays) - 1

            # Track stats
            if possession == team1:
                team1_plays += num_plays
                team1_total_yards += yards_gained
            else:
                team2_plays += num_plays
                team2_total_yards += yards_gained

            # Add plays to game log
            all_plays.extend(drive_plays)

            # Update time
            time_in_quarter -= time_used
            if time_in_quarter < 0:
                time_in_quarter = 0

            # Switch possession
            possession = team2 if possession == team1 else team1

            # Set new field position
            # If offense scored, next team gets kickoff at own 25
            if offense.score > score_before:
                field_pos = 25
            else:
                # Turnover/punt - flip field position
                field_pos = 100 - end_field_pos
                field_pos = max(1, min(99, field_pos))

        # Move to next quarter
        quarter += 1
        time_in_quarter = 900

        if quarter == 3:
            # Second half kickoff - reverse possession
            possession = team2
            field_pos = 25

    # Determine winner
    if team1.score > team2.score:
        winner = team1
    elif team2.score > team1.score:
        winner = team2
    else:
        # NFL Overtime rules
        all_plays.append("\n" + "=" * 70)
        all_plays.append("=== OVERTIME ===")
        all_plays.append("=" * 70)

        # 10-minute overtime period (600 seconds)
        ot_time_remaining = 600
        ot_possession = random.choice([team1, team2])  # Coin toss
        ot_field_pos = 25
        team1_ot_possessions = 0
        team2_ot_possessions = 0

        all_plays.append(f"\n{ot_possession.name} wins the coin toss!")

        winner = None
        while ot_time_remaining > 0 and winner is None:
            ot_offense = ot_possession
            ot_defense = team2 if ot_offense == team1 else team1

            # Track possessions
            if ot_offense == team1:
                team1_ot_possessions += 1
            else:
                team2_ot_possessions += 1

            score_diff_ot = ot_offense.score - ot_defense.score
            score_before_ot = ot_offense.score

            # Simulate OT drive
            drive_plays, end_field_pos, time_used, yards_gained = simulate_drive(
                ot_offense, ot_defense, ot_field_pos, 5, ot_time_remaining, score_diff_ot
            )

            all_plays.extend(drive_plays)
            ot_time_remaining -= time_used

            # Check if offense scored
            if ot_offense.score > score_before_ot:
                points_scored = ot_offense.score - score_before_ot

                # First possession TD wins immediately
                if team1_ot_possessions == 1 and team2_ot_possessions == 0 and points_scored >= 6:
                    winner = ot_offense
                    all_plays.append(f"\n{winner.name} wins with a touchdown on first possession!")
                    break

                # Both teams had possession - any score wins
                elif team1_ot_possessions >= 1 and team2_ot_possessions >= 1:
                    winner = ot_offense
                    all_plays.append(f"\n{winner.name} wins in overtime!")
                    break

                # First possession FG - other team gets a chance
                elif points_scored == 3 and (team1_ot_possessions + team2_ot_possessions) == 1:
                    # Switch possession
                    ot_possession = team2 if ot_possession == team1 else team1
                    ot_field_pos = 25
                    continue

            # No score or time expired, switch possession
            ot_possession = team2 if ot_possession == team1 else team1
            ot_field_pos = 100 - end_field_pos
            ot_field_pos = max(1, min(99, ot_field_pos))

        # If still tied after OT (time expired)
        if winner is None:
            if team1.score > team2.score:
                winner = team1
            elif team2.score > team1.score:
                winner = team2
            else:
                # Still tied - sudden death continues (pick random for simplicity)
                winner = random.choice([team1, team2])
                winner.score += 3
                all_plays.append(f"\n{winner.name} wins in sudden death!")

    # Update team season stats (regular or playoff)
    if is_playoff:
        # Playoff stats don't affect points_for/points_against (those are regular season only)
        # Only track playoff wins/losses
        if winner == team1:
            team1.playoff_wins += 1
            team2.playoff_losses += 1
            team2.eliminated = True
        else:
            team2.playoff_wins += 1
            team1.playoff_losses += 1
            team1.eliminated = True
    else:
        # Regular season stats
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

    # Add game summary to play-by-play
    all_plays.append("\n" + "=" * 70)
    all_plays.append("GAME SUMMARY")
    all_plays.append("=" * 70)
    all_plays.append(f"\n{team1.name}: {team1.score}")
    all_plays.append(f"  Drives: {team1_drives}")
    all_plays.append(f"  Plays: {team1_plays}")
    all_plays.append(f"  Total Yards: {team1_total_yards}")
    all_plays.append(f"\n{team2.name}: {team2.score}")
    all_plays.append(f"  Drives: {team2_drives}")
    all_plays.append(f"  Plays: {team2_plays}")
    all_plays.append(f"  Total Yards: {team2_total_yards}")
    all_plays.append(f"\nTotal Plays: {team1_plays + team2_plays}")

    # Store stats and play-by-play
    _compute_delta_and_store(team1, before_team1, team1.players)
    _compute_delta_and_store(team2, before_team2, team2.players)

    team1.last_game_plays = all_plays
    team2.last_game_plays = all_plays

    # Print result
    if user_team is None or user_team in [team1.name, team2.name]:
        print(f"{team1.name} {team1.score} - {team2.name} {team2.score}")

    return winner
