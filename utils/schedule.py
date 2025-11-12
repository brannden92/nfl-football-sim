"""
Schedule generation utilities for NFL Football Simulation
"""
import random


def generate_season_schedule(teams):
    """
    Generate an 18-week NFL-style schedule with BYE weeks

    Rules:
    - 18 weeks total
    - Each team plays 17 games
    - Each team gets 1 BYE week (no game)
    - 4 teams per week get BYEs from Week 6-13
    - Division opponents play each other twice (6 games for 4-team divisions)
    - Remaining 11 games distributed across conference/league

    Returns:
        dict: schedule[week] = [{'home': team, 'away': team, 'played': False}]
    """

    schedule = {week: [] for week in range(1, 19)}

    # Organize teams by division
    divisions = {}
    for team in teams:
        div_key = (team.league, team.division)
        if div_key not in divisions:
            divisions[div_key] = []
        divisions[div_key].append(team)

    # Track games scheduled for each team
    team_games = {team.name: [] for team in teams}
    team_opponents = {team.name: set() for team in teams}
    team_bye_week = {}  # Track which week each team has BYE

    # Assign BYE weeks (weeks 6-13, 4 teams per week)
    bye_weeks = list(range(6, 14))  # Weeks 6-13
    teams_list = list(teams)
    random.shuffle(teams_list)

    teams_per_bye_week = len(teams_list) // len(bye_weeks)
    for i, team in enumerate(teams_list):
        bye_week_idx = min(i // teams_per_bye_week, len(bye_weeks) - 1)
        team_bye_week[team.name] = bye_weeks[bye_week_idx]

    # Step 1: Schedule division games (each team plays division opponents twice)
    division_matchups = []
    for div_key, div_teams in divisions.items():
        # Each team plays every other team in division twice
        for i, team1 in enumerate(div_teams):
            for team2 in div_teams[i+1:]:
                # Schedule 2 games between these teams
                division_matchups.append((team1, team2, True))   # Home game for team1
                division_matchups.append((team2, team1, True))   # Home game for team2

    # Shuffle division matchups
    random.shuffle(division_matchups)

    # Step 2: Create inter-division/conference matchups for remaining games
    # Each team needs 17 total games, 6 are division games, so 11 more needed
    non_division_matchups = []

    for team1 in teams:
        # Find opponents not in same division
        same_div = [t for t in teams if t.league == team1.league and t.division == team1.division and t != team1]
        other_teams = [t for t in teams if t not in same_div and t != team1]

        # Schedule games with non-division teams
        for team2 in other_teams:
            # Only add if not already scheduled
            if team2.name not in team_opponents[team1.name]:
                non_division_matchups.append((team1, team2, False))

    # Shuffle non-division matchups
    random.shuffle(non_division_matchups)

    # Combine all matchups
    all_matchups = division_matchups + non_division_matchups

    # Step 3: Distribute matchups across weeks
    week = 1
    matchup_idx = 0

    while matchup_idx < len(all_matchups) and week <= 18:
        week_matchups = []
        teams_this_week = set()

        # Add matchups to this week
        attempts = 0
        while matchup_idx < len(all_matchups) and attempts < len(all_matchups) * 2:
            home_team, away_team, is_division = all_matchups[matchup_idx]

            # Check if either team already playing this week
            if home_team.name in teams_this_week or away_team.name in teams_this_week:
                matchup_idx += 1
                attempts += 1
                continue

            # Check if either team has BYE this week
            if team_bye_week.get(home_team.name) == week or team_bye_week.get(away_team.name) == week:
                matchup_idx += 1
                attempts += 1
                continue

            # Check if teams have already played enough games
            if len(team_games[home_team.name]) >= 17 or len(team_games[away_team.name]) >= 17:
                matchup_idx += 1
                attempts += 1
                continue

            # Add this matchup
            week_matchups.append({
                'home': home_team,
                'away': away_team,
                'played': False,
                'home_score': 0,
                'away_score': 0
            })

            teams_this_week.add(home_team.name)
            teams_this_week.add(away_team.name)
            team_games[home_team.name].append(week)
            team_games[away_team.name].append(week)
            team_opponents[home_team.name].add(away_team.name)
            team_opponents[away_team.name].add(home_team.name)

            matchup_idx += 1
            attempts = 0

        schedule[week] = week_matchups
        week += 1

    # Debug: Validate schedule - count games per team
    team_game_counts = {}
    for team in teams:
        game_count = sum(1 for w in schedule.values() for m in w
                        if m['home'].name == team.name or m['away'].name == team.name)
        team_game_counts[team.name] = game_count

    # Print teams with incorrect game counts
    incorrect_counts = {name: count for name, count in team_game_counts.items() if count != 17}
    if incorrect_counts:
        print(f"\n*** WARNING: Some teams don't have exactly 17 games: {incorrect_counts} ***\n")

    return schedule


def get_team_schedule(franchise, team_name):
    """
    Get schedule for a specific team

    Returns:
        list: List of dicts with week, opponent, home/away, result
    """
    team_schedule = []

    for week in range(1, 19):
        if week not in franchise.schedule:
            continue

        week_matchups = franchise.schedule[week]

        # Check if team has a game this week
        game_found = False
        for matchup in week_matchups:
            if matchup['home'].name == team_name:
                team_schedule.append({
                    'week': week,
                    'opponent': matchup['away'].name,
                    'home': True,
                    'played': matchup['played'],
                    'user_score': matchup['home_score'] if matchup['played'] else None,
                    'opp_score': matchup['away_score'] if matchup['played'] else None
                })
                game_found = True
                break
            elif matchup['away'].name == team_name:
                team_schedule.append({
                    'week': week,
                    'opponent': matchup['home'].name,
                    'home': False,
                    'played': matchup['played'],
                    'user_score': matchup['away_score'] if matchup['played'] else None,
                    'opp_score': matchup['home_score'] if matchup['played'] else None
                })
                game_found = True
                break

        if not game_found:
            # BYE week
            team_schedule.append({
                'week': week,
                'opponent': 'BYE',
                'home': None,
                'played': True,
                'user_score': None,
                'opp_score': None
            })

    return team_schedule


def get_next_opponent(franchise, team_name):
    """
    Get the next opponent for a team

    Returns:
        Team or None if no more games
    """
    current_week = franchise.current_week

    if current_week > 18 or current_week not in franchise.schedule:
        return None

    week_matchups = franchise.schedule[current_week]

    for matchup in week_matchups:
        if matchup['home'].name == team_name:
            return matchup['away']
        elif matchup['away'].name == team_name:
            return matchup['home']

    # BYE week
    return None
