"""
Statistics display utilities for the NFL Football Simulation
"""
from prettytable import PrettyTable


def calculate_team_ratings(team, games_played):
    """Calculate offensive and defensive ratings for a team"""

    # If no games played, calculate ratings based on player skills
    if games_played == 0:
        # Passing offense: Based on QB + receivers
        if team.qb_starters:
            qb_skill = sum(qb.skill for qb in team.qb_starters) / len(team.qb_starters)
            receiver_skill = 0
            receivers = team.wr_starters + team.te_starters
            if receivers:
                receiver_skill = sum(r.skill for r in receivers) / len(receivers)
            pass_off = int((qb_skill * 0.6 + receiver_skill * 0.4))
        else:
            pass_off = 50

        # Rushing offense: Based on RBs
        if team.rb_starters:
            rb_skill = sum(rb.skill for rb in team.rb_starters) / len(team.rb_starters)
            rush_off = int(rb_skill)
        else:
            rush_off = 50

        # Defense: Based on defensive players
        if team.defense_starters:
            def_skill = sum(d.skill for d in team.defense_starters) / len(team.defense_starters)
            pass_def = int(def_skill)
            rush_def = int(def_skill)
        else:
            pass_def = 50
            rush_def = 50

        # Special teams: Based on kicker and punter
        kicker_rating = 0
        punter_rating = 0
        if team.k_starters:
            kicker = team.k_starters[0]
            kicker_rating = (getattr(kicker, 'kicking_power', kicker.skill) +
                           getattr(kicker, 'kicking_accuracy', kicker.skill)) / 2
        if team.p_starters:
            punter = team.p_starters[0]
            punter_rating = (getattr(punter, 'kicking_power', punter.skill) +
                           getattr(punter, 'kicking_accuracy', punter.skill)) / 2

        if kicker_rating > 0 and punter_rating > 0:
            special_teams = int((kicker_rating + punter_rating) / 2)
        elif kicker_rating > 0:
            special_teams = int(kicker_rating)
        elif punter_rating > 0:
            special_teams = int(punter_rating)
        else:
            special_teams = 50

        return {
            'pass_off': max(30, min(99, pass_off)),
            'rush_off': max(30, min(99, rush_off)),
            'pass_def': max(30, min(99, pass_def)),
            'rush_def': max(30, min(99, rush_def)),
            'special_teams': max(30, min(99, special_teams))
        }

    # Calculate passing offense rating (yards per game and TD/INT ratio)
    qb_stats = team.qb_starters[0] if team.qb_starters else None
    if qb_stats and qb_stats.pass_attempts > 0:
        pass_ypg = qb_stats.pass_yards / games_played
        td_int_ratio = qb_stats.pass_td / max(1, qb_stats.interceptions)
        pass_off = min(99, int(50 + (pass_ypg - 200) / 5 + td_int_ratio * 3))
    else:
        pass_off = 50

    # Calculate rushing offense rating (yards per game and YPA)
    total_rush_yards = sum(p.rush_yards for p in team.rb_starters + team.qb_starters)
    total_rush_att = sum(p.rush_attempts for p in team.rb_starters + team.qb_starters)
    if total_rush_att > 0:
        rush_ypg = total_rush_yards / games_played
        rush_ypa = total_rush_yards / total_rush_att
        rush_off = min(99, int(50 + (rush_ypg - 100) / 3 + (rush_ypa - 4) * 5))
    else:
        rush_off = 50

    # Calculate defensive ratings (inverse of points allowed)
    ppg_allowed = team.points_against / games_played if games_played > 0 else 20
    pass_def = min(99, int(90 - ppg_allowed))
    rush_def = min(99, int(90 - ppg_allowed))

    # Special teams rating (placeholder - could be based on field position, etc.)
    special_teams = 50

    return {
        'pass_off': max(30, min(99, pass_off)),
        'rush_off': max(30, min(99, rush_off)),
        'pass_def': max(30, min(99, pass_def)),
        'rush_def': max(30, min(99, rush_def)),
        'special_teams': special_teams
    }


def print_opponent_preview(user_team, opponent, all_teams, games_played):
    """Print a preview of the weekly opponent"""
    print(f"\n{'=' * 70}")
    print(f"WEEK {games_played + 1} OPPONENT PREVIEW".center(70))
    print(f"{'=' * 70}")

    # Basic team info
    print(f"\n{opponent.name}")
    print(f"{'-' * 70}")
    print(f"Record: {opponent.wins}-{opponent.losses}")
    print(f"Points For: {opponent.points_for} (PF)")
    print(f"Points Against: {opponent.points_against} (PA)")
    print(f"Point Differential: {opponent.points_for - opponent.points_against:+d} (PD)")

    # Division standing
    div_teams = [t for t in all_teams if t.league == opponent.league and t.division == opponent.division]
    div_teams_sorted = sorted(div_teams, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    div_rank = div_teams_sorted.index(opponent) + 1
    print(f"Division Standing: {div_rank}{get_ordinal(div_rank)} in {opponent.league} {opponent.division}")

    # Top 3 rated players
    print(f"\n{'Top Players:'}")
    all_players = sorted(opponent.players, key=lambda p: p.skill, reverse=True)[:3]
    for i, player in enumerate(all_players, 1):
        print(f"  {i}. {player.name} ({player.position}) - Skill: {player.skill}")

    # Team ratings with rankings
    print(f"\n{'Team Ratings:'}")
    ratings = calculate_team_ratings(opponent, games_played)
    rating_labels = {
        'pass_off': 'Pass Offense',
        'rush_off': 'Rush Offense',
        'pass_def': 'Pass Defense',
        'rush_def': 'Rush Defense',
        'special_teams': 'Special Teams'
    }

    # Calculate all team ratings for ranking
    all_ratings = {}
    for team in all_teams:
        team_ratings = calculate_team_ratings(team, games_played)
        all_ratings[team.name] = team_ratings

    # Display ratings with rankings
    for key, label in rating_labels.items():
        rating = ratings[key]
        bar_length = int(rating / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)

        # Calculate rank for this rating category
        sorted_teams = sorted(all_ratings.items(), key=lambda x: x[1][key], reverse=True)
        rank = next(i + 1 for i, (name, _) in enumerate(sorted_teams) if name == opponent.name)

        print(f"  {label:15s}: {bar} {rating}/99 ({rank}{get_ordinal(rank)})")

    print(f"{'=' * 70}\n")


def get_ordinal(n):
    """Return ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
    if 11 <= n % 100 <= 13:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


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

    print(f"\n{'=' * 70}")
    print(f"{'YOUR TEAM: ' + team.name:^70}")
    print(f"{'=' * 70}")
    print(f"Record: {team.wins}-{team.losses} | {team.league} {team.division} | {div_rank}{get_ordinal(div_rank)} in Division")
    print(f"Points For: {team.points_for} (Rank: {offense_rank}{get_ordinal(offense_rank)})")
    print(f"Points Against: {team.points_against} (Rank: {defense_rank}{get_ordinal(defense_rank)})")
    print(f"Point Differential: {team.points_for - team.points_against:+d}")
    print(f"{'=' * 70}\n")


def print_team_stats(team, games_played):
    """Print season stats for a team"""
    print(f"\n=== SEASON STATS (Through {games_played} Games) ===")

    print("\n=== Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Comp", "Att", "Comp%", "Yards", "TD", "INT", "Y/A", "YPG", "Long", "Sacks"]
    qbs = sorted(team.qb_starters, key=lambda x: x.pass_yards, reverse=True)
    for qb in qbs:
        comp_pct = qb.pass_completions / qb.pass_attempts * 100 if qb.pass_attempts else 0
        ypa = qb.pass_yards / qb.pass_attempts if qb.pass_attempts else 0
        ypg = qb.pass_yards / games_played if games_played > 0 else 0
        table.add_row([
            qb.name, qb.pass_completions, qb.pass_attempts, round(comp_pct, 1), qb.pass_yards,
            qb.pass_td, qb.interceptions, round(ypa, 1), round(ypg, 1), qb.longest_pass, qb.sacks_taken
        ])
    print(table)

    print("\n=== Rushing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Att", "Yards", "TD", "Y/A", "YPG", "Long", "Fum"]
    # Include QBs and RBs
    rushers = team.qb_starters + team.rb_starters
    rushers = [r for r in rushers if r.rush_attempts > 0]
    rushers.sort(key=lambda x: x.rush_yards, reverse=True)
    rushers = rushers[:3]  # Top 3 rushers

    for rusher in rushers:
        ya = rusher.rush_yards / rusher.rush_attempts if rusher.rush_attempts else 0
        ypg = rusher.rush_yards / games_played if games_played > 0 else 0
        table.add_row([
            rusher.name, rusher.rush_attempts, rusher.rush_yards, rusher.rush_td,
            round(ya, 1), round(ypg, 1), rusher.longest_rush, rusher.fumbles
        ])
    print(table)

    print("\n=== Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Rec", "Targets", "Yards", "TD", "Y/R", "YPG", "Long", "Drops"]
    # Include RBs in receiving stats
    receivers = team.wr_starters + team.te_starters + team.rb_starters
    receivers = [r for r in receivers if r.rec_targets > 0]
    receivers.sort(key=lambda x: x.rec_yards, reverse=True)
    receivers = receivers[:6]  # Top 6 receivers

    for r in receivers:
        ypr = r.rec_yards / r.rec_catches if r.rec_catches else 0
        ypg = r.rec_yards / games_played if games_played > 0 else 0
        table.add_row([
            r.name, r.rec_catches, r.rec_targets, r.rec_yards, r.rec_td,
            round(ypr, 1), round(ypg, 1), r.longest_rec, r.drops
        ])
    print(table)

    print("\n=== Defensive Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Tackles", "Sacks", "QB Pressure", "INT", "FF", "FR", "PD"]
    defenders = sorted(team.defense_starters, key=lambda x: (x.tackles + x.sacks), reverse=True)[:5]
    for d in defenders:
        table.add_row([
            d.name, d.tackles, d.sacks, d.qb_pressure, d.interceptions_def,
            d.forced_fumbles, d.fumble_recoveries, d.pass_deflections
        ])
    print(table)


def print_last_game_stats(team):
    """Print leaders/tables for the last game using team.last_game_stats (deltas)."""
    if not getattr(team, "last_game_stats", None):
        print("\nNo last game stats available for this team yet.")
        return

    lg = team.last_game_stats

    # Passing leaders (last game)
    print("\n=== LAST GAME: Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Player", "Comp", "Att", "Yds", "TD", "INT", "Comp%", "Y/A", "Long"]
    # find QBs present in last_game_stats
    qbs = [p for p in team.players if p.position == "QB"]
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
    table.field_names = ["Player", "Att", "Yds", "TD", "Y/A", "Long"]
    rbs = [p for p in team.players if p.position == "RB"] + [p for p in team.players if p.position == "QB"]
    rbs_sorted = sorted(rbs, key=lambda x: lg.get(x.name, {}).get("rush_yards", 0), reverse=True)[:3]
    for r in rbs_sorted:
        d = lg.get(r.name, {})
        att = d.get("rush_attempts", 0)
        yds = d.get("rush_yards", 0)
        td = d.get("rush_td", 0)
        ya = round(yds / att, 1) if att else 0
        table.add_row([r.name, att, yds, td, ya, d.get("longest_rush", 0)])
    print(table)

    # Receiving leaders (last game)
    print("\n=== LAST GAME: Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Player", "Catches", "Targets", "Yds", "TD", "Y/R", "Drops", "Long"]
    recs = [p for p in team.players if p.position in ["WR", "TE", "RB"]]
    recs_sorted = sorted(recs, key=lambda x: lg.get(x.name, {}).get("rec_yards", 0), reverse=True)[:6]
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
    table.field_names = ["Player", "Tkl", "Sacks", "QB Press", "INT", "FF", "FR", "PD"]
    defs = team.defense_starters
    defs_sorted = sorted(
        defs,
        key=lambda x: lg.get(x.name, {}).get("tackles", 0) + lg.get(x.name, {}).get("sacks", 0),
        reverse=True
    )[:5]
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


def print_career_stats(team):
    """Print career stats for team's players"""
    print(f"\n=== CAREER STATS: {team.name} ===")

    # Career passing leaders
    print("\n=== Career Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Years", "Comp", "Att", "Comp%", "Yards", "TD", "INT", "Long"]
    qbs = [p for p in team.players if p.position == "QB" and p.career_stats.get("pass_attempts", 0) > 0]
    qbs.sort(key=lambda x: x.career_stats.get("pass_yards", 0), reverse=True)

    for qb in qbs[:5]:  # Top 5
        cs = qb.career_stats
        att = cs.get("pass_attempts", 0)
        comp = cs.get("pass_completions", 0)
        comp_pct = round(100 * comp / att, 1) if att > 0 else 0
        table.add_row([
            qb.name, qb.years_played, comp, att, comp_pct,
            cs.get("pass_yards", 0), cs.get("pass_td", 0),
            cs.get("interceptions", 0), cs.get("longest_pass", 0)
        ])
    print(table)

    # Career rushing leaders
    print("\n=== Career Rushing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Years", "Att", "Yards", "TD", "Y/A", "Long"]
    rushers = [p for p in team.players if p.career_stats.get("rush_attempts", 0) > 0]
    rushers.sort(key=lambda x: x.career_stats.get("rush_yards", 0), reverse=True)

    for rusher in rushers[:5]:  # Top 5
        cs = rusher.career_stats
        att = cs.get("rush_attempts", 0)
        yards = cs.get("rush_yards", 0)
        ya = round(yards / att, 1) if att > 0 else 0
        table.add_row([
            rusher.name, rusher.years_played, att, yards,
            cs.get("rush_td", 0), ya, cs.get("longest_rush", 0)
        ])
    print(table)

    # Career receiving leaders
    print("\n=== Career Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Years", "Rec", "Yards", "TD", "Y/R", "Long"]
    receivers = [p for p in team.players if p.career_stats.get("rec_catches", 0) > 0]
    receivers.sort(key=lambda x: x.career_stats.get("rec_yards", 0), reverse=True)

    for receiver in receivers[:5]:  # Top 5
        cs = receiver.career_stats
        catches = cs.get("rec_catches", 0)
        yards = cs.get("rec_yards", 0)
        ypr = round(yards / catches, 1) if catches > 0 else 0
        table.add_row([
            receiver.name, receiver.years_played, catches, yards,
            cs.get("rec_td", 0), ypr, cs.get("longest_rec", 0)
        ])
    print(table)

    # Career defensive leaders
    print("\n=== Career Defensive Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name", "Years", "Tackles", "Sacks", "INT", "FF", "FR"]
    defenders = [p for p in team.players if p.career_stats.get("tackles", 0) > 0]
    defenders.sort(key=lambda x: x.career_stats.get("tackles", 0) + x.career_stats.get("sacks", 0), reverse=True)

    for defender in defenders[:5]:  # Top 5
        cs = defender.career_stats
        table.add_row([
            defender.name, defender.years_played, cs.get("tackles", 0),
            cs.get("sacks", 0), cs.get("interceptions_def", 0),
            cs.get("forced_fumbles", 0), cs.get("fumble_recoveries", 0)
        ])
    print(table)


def view_last_game_plays(team):
    """Display play-by-play from the last game"""
    if not hasattr(team, 'last_game_plays') or not team.last_game_plays:
        print("\nNo play-by-play data available for the last game.")
        return

    print(f"\n{'=' * 70}")
    print(f"LAST GAME PLAY-BY-PLAY".center(70))
    print(f"{'=' * 70}")

    for play in team.last_game_plays:
        print(play)

    print(f"{'=' * 70}\n")


def calculate_team_stats(team, games_played):
    """Calculate team statistics for web display"""
    if games_played == 0:
        return {
            'ppg': '0.0',
            'papg': '0.0',
            'pass_ypg': '0',
            'pass_yapg': 'N/A',
            'pass_tds_for': 0,
            'pass_tds_against': 0,
            'rush_ypg': '0',
            'rush_yapg': 'N/A',
            'rush_tds_for': 0,
            'rush_tds_against': 0,
            'fg_pct': 'N/A',
            'longest_fg': 0,
            'avg_punt': 'N/A'
        }

    # Points per game
    ppg = round(team.points_for / games_played, 1)
    papg = round(team.points_against / games_played, 1)

    # Passing stats
    total_pass_yards = sum(p.pass_yards for p in team.qb_starters)
    pass_ypg = round(total_pass_yards / games_played) if games_played > 0 else 0
    pass_tds_for = sum(p.pass_td for p in team.qb_starters)

    # Rushing stats
    total_rush_yards = sum(p.rush_yards for p in team.rb_starters + team.qb_starters)
    rush_ypg = round(total_rush_yards / games_played) if games_played > 0 else 0
    rush_tds_for = sum(p.rush_td for p in team.rb_starters + team.qb_starters)

    # Defensive stats (TDs allowed - placeholder for now)
    pass_tds_against = 0  # Would need opponent data
    rush_tds_against = 0  # Would need opponent data
    pass_yapg = 'N/A'  # Would need opponent data
    rush_yapg = 'N/A'  # Would need opponent data

    # Special teams stats
    if team.k_starters:
        kicker = team.k_starters[0]
        # Placeholder - would need actual FG attempts/makes tracking
        fg_pct = 'N/A'
        longest_fg = getattr(kicker, 'longest_fg', 0) if hasattr(kicker, 'longest_fg') else 0
    else:
        fg_pct = 'N/A'
        longest_fg = 0

    if team.p_starters:
        punter = team.p_starters[0]
        # Placeholder - would need actual punt tracking
        avg_punt = 'N/A'
    else:
        avg_punt = 'N/A'

    return {
        'ppg': ppg,
        'papg': papg,
        'pass_ypg': pass_ypg,
        'pass_yapg': pass_yapg,
        'pass_tds_for': pass_tds_for,
        'pass_tds_against': pass_tds_against,
        'rush_ypg': rush_ypg,
        'rush_yapg': rush_yapg,
        'rush_tds_for': rush_tds_for,
        'rush_tds_against': rush_tds_against,
        'fg_pct': fg_pct,
        'longest_fg': longest_fg,
        'avg_punt': avg_punt
    }


def get_top_players(team, games_played):
    """Get top players for web display with their season stats"""
    top_players = []

    # QB - Top QB by passing yards
    if team.qb_starters:
        qb = max(team.qb_starters, key=lambda p: p.pass_yards)
        if games_played > 0:
            comp_pct = round(qb.pass_completions / qb.pass_attempts * 100, 1) if qb.pass_attempts > 0 else 0
            pass_ypg = round(qb.pass_yards / games_played, 1)
            rush_ypa = round(qb.rush_yards / qb.rush_attempts, 1) if qb.rush_attempts > 0 else 0
            stats_line = f"Pass: {qb.pass_completions}/{qb.pass_attempts} ({comp_pct}%), {pass_ypg} ypg, {qb.pass_td} TD, {qb.interceptions} INT | Rush: {qb.rush_attempts} att, {qb.rush_yards} yds ({rush_ypa} avg), {qb.rush_td} TD"
        else:
            stats_line = "No stats yet"
        top_players.append({
            'position': 'QB',
            'name': qb.name,
            'skill': qb.skill,
            'stats_line': stats_line
        })

    # RB - Top RB by rushing yards
    if team.rb_starters:
        rb = max(team.rb_starters, key=lambda p: p.rush_yards)
        if games_played > 0:
            ypa = round(rb.rush_yards / rb.rush_attempts, 1) if rb.rush_attempts > 0 else 0
            stats_line = f"{rb.rush_attempts} att, {rb.rush_yards} yds ({ypa} avg), {rb.rush_td} TD"
        else:
            stats_line = "No stats yet"
        top_players.append({
            'position': 'RB',
            'name': rb.name,
            'skill': rb.skill,
            'stats_line': stats_line
        })

    # WR - Top WR by receiving yards
    if team.wr_starters:
        wr = max(team.wr_starters, key=lambda p: p.rec_yards)
        if games_played > 0:
            ypc = round(wr.rec_yards / wr.rec_catches, 1) if wr.rec_catches > 0 else 0
            stats_line = f"{wr.rec_catches} rec, {wr.rec_yards} yds ({ypc} avg), {wr.rec_td} TD"
        else:
            stats_line = "No stats yet"
        top_players.append({
            'position': 'WR',
            'name': wr.name,
            'skill': wr.skill,
            'stats_line': stats_line
        })

    # TE - Top TE by receiving yards
    if team.te_starters:
        te = max(team.te_starters, key=lambda p: p.rec_yards)
        if games_played > 0:
            ypc = round(te.rec_yards / te.rec_catches, 1) if te.rec_catches > 0 else 0
            stats_line = f"{te.rec_catches} rec, {te.rec_yards} yds ({ypc} avg), {te.rec_td} TD"
        else:
            stats_line = "No stats yet"
        top_players.append({
            'position': 'TE',
            'name': te.name,
            'skill': te.skill,
            'stats_line': stats_line
        })

    # Top 3 defensive players by combined tackles + sacks
    if team.defense_starters:
        top_defenders = sorted(team.defense_starters, key=lambda p: p.tackles + p.sacks, reverse=True)[:3]
        for defender in top_defenders:
            if games_played > 0:
                stats_line = f"{defender.tackles} tkl, {defender.sacks} sacks, {defender.interceptions_def} INT"
            else:
                stats_line = "No stats yet"
            top_players.append({
                'position': defender.position,
                'name': defender.name,
                'skill': defender.skill,
                'stats_line': stats_line
            })

    # Kicker
    if team.k_starters:
        k = team.k_starters[0]
        if games_played > 0:
            stats_line = "Stats tracking coming soon"
        else:
            stats_line = "No stats yet"
        top_players.append({
            'position': 'K',
            'name': k.name,
            'skill': k.skill,
            'stats_line': stats_line
        })

    return top_players
