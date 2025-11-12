"""
Flask web application for NFL Football Simulation
"""
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import pickle
import os
import random
from models import Franchise
from game import simulate_game, run_playoffs
from utils import (
    create_new_league, save_franchise, load_franchise,
    print_team_summary, calculate_team_ratings, calculate_team_stats,
    get_top_players, calculate_stat_rankings, view_standings,
    generate_draft_prospects, run_scouting, run_draft
)
from config import SEASON_GAMES

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Global franchise storage (in production, use a database)
FRANCHISE_FILE = 'web_franchise.pkl'


def get_franchise():
    """Get current franchise from session or file"""
    if os.path.exists(FRANCHISE_FILE):
        with open(FRANCHISE_FILE, 'rb') as f:
            franchise = pickle.load(f)

            # Compatibility: Add schedule if it doesn't exist (for old saves)
            if not hasattr(franchise, 'schedule') or not franchise.schedule:
                from utils.schedule import generate_season_schedule
                print(f"\n*** GENERATING NEW SCHEDULE for franchise at week {franchise.current_week} ***")
                franchise.schedule = generate_season_schedule(franchise.teams)
                print(f"*** Schedule generated with weeks: {sorted(franchise.schedule.keys())} ***\n")

                # Mark past weeks as played (for mid-season migrations)
                past_weeks_marked = 0
                for week in range(1, franchise.current_week):
                    if week in franchise.schedule:
                        for matchup in franchise.schedule[week]:
                            matchup['played'] = True
                            # Set placeholder scores for past games
                            matchup['home_score'] = matchup['home'].score
                            matchup['away_score'] = matchup['away'].score
                        past_weeks_marked += 1

                if past_weeks_marked > 0:
                    print(f"*** Marked {past_weeks_marked} past weeks as played ***\n")

            # Compatibility: Ensure all teams have last_game_player_stats
            for team in franchise.teams:
                if not hasattr(team, 'last_game_player_stats'):
                    team.last_game_player_stats = {}

                # Compatibility: Ensure all players have returning attribute
                for player in team.players:
                    if not hasattr(player, 'returning'):
                        # Set returning skill based on position
                        if player.position in ["RB", "WR", "CB"]:
                            player.returning = min(99, max(60, player.skill + random.randint(-5, 5)))
                            player.returning_potential = min(99, player.returning + random.randint(5, 15))
                        else:
                            player.returning = min(75, max(40, player.skill - 10 + random.randint(-5, 5)))
                            player.returning_potential = min(80, player.returning + random.randint(3, 10))

                    # Ensure return stats exist
                    if not hasattr(player, 'kickoff_returns'):
                        player.kickoff_returns = 0
                        player.kickoff_return_yards = 0
                        player.longest_kickoff_return = 0
                        player.punt_returns = 0
                        player.punt_return_yards = 0
                        player.longest_punt_return = 0

                        # Add to career stats if missing
                        if 'kickoff_returns' not in player.career_stats:
                            player.career_stats['kickoff_returns'] = 0
                            player.career_stats['kickoff_return_yards'] = 0
                            player.career_stats['longest_kickoff_return'] = 0
                            player.career_stats['punt_returns'] = 0
                            player.career_stats['punt_return_yards'] = 0
                            player.career_stats['longest_punt_return'] = 0

            # Save the updated franchise
            save_current_franchise(franchise)

            return franchise
    return None


def save_current_franchise(franchise):
    """Save franchise to file"""
    with open(FRANCHISE_FILE, 'wb') as f:
        pickle.dump(franchise, f)


def get_user_team(franchise):
    """Get the user's team from franchise"""
    return next((t for t in franchise.teams if t.name == franchise.user_team_name), None)


def _get_playoff_opponent(franchise, user_team):
    """Determine user's next playoff opponent based on current playoff state"""
    if not franchise.playoff_state or user_team.eliminated:
        return None

    user_conf = user_team.league  # AFC or NFC
    user_seed = user_team.playoff_seed

    if franchise.playoff_state == 'wildcard':
        # Find user's wild card matchup
        matchups = franchise.playoff_bracket['wildcard'][user_conf.lower()]
        for matchup in matchups:
            if matchup['seed1'] == user_seed:
                # User is higher seed (home team)
                opponent_seed = matchup['seed2']
            elif matchup['seed2'] == user_seed:
                # User is lower seed (away team)
                opponent_seed = matchup['seed1']
            else:
                continue

            # Find team with this seed
            opponent = next((t for t in franchise.teams
                           if t.league == user_conf and t.playoff_seed == opponent_seed), None)
            return opponent

    elif franchise.playoff_state == 'divisional':
        # Find user's divisional matchup
        matchups = franchise.playoff_bracket['divisional'][user_conf.lower()]
        for matchup in matchups:
            team1_seed = matchup.get('seed1')
            team2_seed = matchup.get('seed2')
            if team1_seed == user_seed or team2_seed == user_seed:
                opponent_seed = team2_seed if team1_seed == user_seed else team1_seed
                opponent = next((t for t in franchise.teams
                               if t.league == user_conf and t.playoff_seed == opponent_seed), None)
                return opponent

    elif franchise.playoff_state == 'conference':
        # Find user's conference championship opponent
        matchups = franchise.playoff_bracket['conference'][user_conf.lower()]
        if matchups:
            matchup = matchups[0]
            team1_seed = matchup.get('seed1')
            team2_seed = matchup.get('seed2')
            if team1_seed == user_seed or team2_seed == user_seed:
                opponent_seed = team2_seed if team1_seed == user_seed else team1_seed
                opponent = next((t for t in franchise.teams
                               if t.league == user_conf and t.playoff_seed == opponent_seed), None)
                return opponent

    elif franchise.playoff_state == 'superbowl':
        # Find Super Bowl opponent (team from other conference)
        matchup = franchise.playoff_bracket.get('superbowl', [])
        if matchup and isinstance(matchup, list) and len(matchup) > 0:
            matchup = matchup[0]
            team1_seed = matchup.get('seed1')
            team2_seed = matchup.get('seed2')
            team1_conf = matchup.get('conf1')
            team2_conf = matchup.get('conf2')

            if team1_conf == user_conf and team1_seed == user_seed:
                opponent = next((t for t in franchise.teams
                               if t.league == team2_conf and t.playoff_seed == team2_seed), None)
                return opponent
            elif team2_conf == user_conf and team2_seed == user_seed:
                opponent = next((t for t in franchise.teams
                               if t.league == team1_conf and t.playoff_seed == team1_seed), None)
                return opponent

    return None


def _simulate_playoff_round(franchise, user_team, user_opponent, other_games):
    """Simulate all other playoff games in the current round"""
    if not franchise.playoff_state:
        return

    # Get all playoff teams
    playoff_teams = [t for t in franchise.teams if hasattr(t, 'playoff_seed') and t.playoff_seed is not None]

    if franchise.playoff_state == 'wildcard':
        # Simulate wild card games
        for conf in ['afc', 'nfc']:
            matchups = franchise.playoff_bracket['wildcard'][conf]
            for matchup in matchups:
                # Get teams for this matchup
                team1 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed1']), None)
                team2 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed2']), None)

                # Skip if this is the user's game (already simulated)
                if team1 in [user_team, user_opponent] or team2 in [user_team, user_opponent]:
                    continue

                if team1 and team2:
                    winner = simulate_game(team1, team2, user_team=None, is_playoff=True)
                    other_games.append({
                        'team1': team1.name,
                        'team1_score': team1.score,
                        'team2': team2.name,
                        'team2_score': team2.score,
                        'playoff_round': 'Wild Card'
                    })

    elif franchise.playoff_state == 'divisional':
        # Simulate divisional games
        for conf in ['afc', 'nfc']:
            matchups = franchise.playoff_bracket['divisional'][conf]
            for matchup in matchups:
                team1 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed1']), None)
                team2 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed2']), None)

                if team1 in [user_team, user_opponent] or team2 in [user_team, user_opponent]:
                    continue

                if team1 and team2 and not team1.eliminated and not team2.eliminated:
                    winner = simulate_game(team1, team2, user_team=None, is_playoff=True)
                    other_games.append({
                        'team1': team1.name,
                        'team1_score': team1.score,
                        'team2': team2.name,
                        'team2_score': team2.score,
                        'playoff_round': 'Divisional'
                    })

    elif franchise.playoff_state == 'conference':
        # Simulate conference championships
        for conf in ['afc', 'nfc']:
            matchups = franchise.playoff_bracket['conference'][conf]
            if matchups:
                matchup = matchups[0]
                team1 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed1']), None)
                team2 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed2']), None)

                if team1 in [user_team, user_opponent] or team2 in [user_team, user_opponent]:
                    continue

                if team1 and team2 and not team1.eliminated and not team2.eliminated:
                    winner = simulate_game(team1, team2, user_team=None, is_playoff=True)
                    other_games.append({
                        'team1': team1.name,
                        'team1_score': team1.score,
                        'team2': team2.name,
                        'team2_score': team2.score,
                        'playoff_round': 'Conference Championship'
                    })


def _advance_playoff_bracket(franchise, user_team):
    """Advance playoff bracket after user's game"""
    if user_team.eliminated:
        # User lost - season over
        franchise.season_complete = True
        return

    user_conf = user_team.league.lower()

    if franchise.playoff_state == 'wildcard':
        # Collect wild card winners
        for conf in ['afc', 'nfc']:
            winners = [t for t in franchise.teams
                      if t.league == conf.upper()
                      and hasattr(t, 'playoff_seed')
                      and t.playoff_seed is not None
                      and not t.eliminated
                      and t.playoff_wins > 0]

            # Add #1 seed (gets bye)
            seed1 = next((t for t in franchise.teams
                         if t.league == conf.upper() and t.playoff_seed == 1), None)
            if seed1 and not seed1.eliminated:
                winners.insert(0, seed1)

            franchise.playoff_bracket['wildcard_winners'][conf] = winners

        # Generate divisional matchups
        for conf in ['afc', 'nfc']:
            winners = franchise.playoff_bracket['wildcard_winners'][conf]
            if len(winners) >= 4:
                # Re-seed: #1 plays lowest, #2 plays next lowest
                seeds = sorted([t.playoff_seed for t in winners])
                franchise.playoff_bracket['divisional'][conf] = [
                    {'seed1': seeds[0], 'seed2': seeds[3]},  # 1 vs lowest
                    {'seed1': seeds[1], 'seed2': seeds[2]}   # 2 vs next
                ]

        franchise.playoff_state = 'divisional'

    elif franchise.playoff_state == 'divisional':
        # Collect divisional winners
        for conf in ['afc', 'nfc']:
            winners = [t for t in franchise.teams
                      if t.league == conf.upper()
                      and hasattr(t, 'playoff_seed')
                      and not t.eliminated
                      and t.playoff_wins >= 2]  # Won wild card + divisional
            franchise.playoff_bracket['divisional_winners'][conf] = winners

        # Generate conference championship matchups
        for conf in ['afc', 'nfc']:
            winners = franchise.playoff_bracket['divisional_winners'][conf]
            if len(winners) >= 2:
                seeds = sorted([t.playoff_seed for t in winners])
                franchise.playoff_bracket['conference'][conf] = [
                    {'seed1': seeds[0], 'seed2': seeds[1]}
                ]

        franchise.playoff_state = 'conference'

    elif franchise.playoff_state == 'conference':
        # Collect conference champions
        afc_champ = next((t for t in franchise.teams
                         if t.league == 'AFC' and not t.eliminated and t.playoff_wins >= 3), None)
        nfc_champ = next((t for t in franchise.teams
                         if t.league == 'NFC' and not t.eliminated and t.playoff_wins >= 3), None)

        if afc_champ and nfc_champ:
            franchise.playoff_bracket['superbowl'] = [{
                'seed1': afc_champ.playoff_seed,
                'seed2': nfc_champ.playoff_seed,
                'conf1': 'AFC',
                'conf2': 'NFC'
            }]
            franchise.playoff_state = 'superbowl'

    elif franchise.playoff_state == 'superbowl':
        # Super Bowl complete - season over
        franchise.season_complete = True


@app.route('/')
def index():
    """Home page / dashboard"""
    franchise = get_franchise()

    if not franchise:
        return redirect(url_for('setup'))

    user_team = get_user_team(franchise)

    # Calculate team ratings
    games_played = franchise.current_week - 1
    ratings = calculate_team_ratings(user_team, games_played)
    user_stats = calculate_team_stats(user_team, games_played)

    # Get division standings with games back
    div_teams = [t for t in franchise.teams if t.league == user_team.league and t.division == user_team.division]
    div_teams.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)

    # Calculate games back for each team
    if div_teams:
        leader_wins = div_teams[0].wins
        leader_losses = div_teams[0].losses
        for team in div_teams:
            gb = ((leader_wins - team.wins) + (team.losses - leader_losses)) / 2.0
            team.games_back = gb if gb > 0 else 0

    # Get next opponent with full scouting info
    next_opponent = None
    next_opponent_ratings = None
    next_opponent_stats = None

    # Check if playoffs should start
    if franchise.current_week > SEASON_GAMES and franchise.playoff_state is None and not franchise.season_complete:
        # Initialize playoffs
        from game.playoffs import get_playoff_teams

        afc_teams = get_playoff_teams([t for t in franchise.teams if t.league == "AFC"])
        nfc_teams = get_playoff_teams([t for t in franchise.teams if t.league == "NFC"])

        # Assign playoff seeds
        for i, team in enumerate(afc_teams, 1):
            team.playoff_seed = i
        for i, team in enumerate(nfc_teams, 1):
            team.playoff_seed = i

        # Check if user made playoffs
        if user_team in afc_teams or user_team in nfc_teams:
            # User made playoffs - set to wild card round
            franchise.playoff_state = 'wildcard'

            # Generate wild card matchups
            franchise.playoff_bracket = {
                'wildcard': {
                    'afc': [
                        {'seed1': 2, 'seed2': 7},
                        {'seed1': 3, 'seed2': 6},
                        {'seed1': 4, 'seed2': 5}
                    ],
                    'nfc': [
                        {'seed1': 2, 'seed2': 7},
                        {'seed1': 3, 'seed2': 6},
                        {'seed1': 4, 'seed2': 5}
                    ]
                },
                'wildcard_winners': {'afc': [], 'nfc': []},
                'divisional': {'afc': [], 'nfc': []},
                'divisional_winners': {'afc': [], 'nfc': []},
                'conference': {'afc': [], 'nfc': []},
                'superbowl': []
            }
        else:
            # User didn't make playoffs - season over
            franchise.season_complete = True

        # Save franchise after playoff initialization
        save_current_franchise(franchise)

    if franchise.current_week <= SEASON_GAMES:
        # Regular season - use schedule to get next opponent
        from utils.schedule import get_next_opponent as schedule_get_next_opponent

        # Debug: Check schedule status
        print(f"\n{'='*60}")
        print(f"DEBUG: Current week: {franchise.current_week}, SEASON_GAMES: {SEASON_GAMES}")
        print(f"DEBUG: Schedule has weeks: {sorted(franchise.schedule.keys())}")

        if franchise.current_week in franchise.schedule:
            week_matchups = franchise.schedule[franchise.current_week]
            print(f"DEBUG: Week {franchise.current_week} has {len(week_matchups)} matchups")

            # Find user's matchup
            user_matchup = None
            for matchup in week_matchups:
                if matchup['home'].name == user_team.name or matchup['away'].name == user_team.name:
                    user_matchup = matchup
                    break

            if user_matchup:
                opp_name = user_matchup['away'].name if user_matchup['home'].name == user_team.name else user_matchup['home'].name
                print(f"DEBUG: User ({user_team.name}) plays {opp_name} this week")
            else:
                print(f"DEBUG: User ({user_team.name}) has no matchup this week (BYE week?)")
        else:
            print(f"WARNING: Week {franchise.current_week} not in schedule!")
        print(f"{'='*60}\n")

        next_opponent = schedule_get_next_opponent(franchise, user_team.name)

        if next_opponent:
            print(f"DEBUG: Found opponent for week {franchise.current_week}: {next_opponent.name}")
            next_opponent_ratings = calculate_team_ratings(next_opponent, games_played)
            next_opponent_stats = calculate_team_stats(next_opponent, games_played)
        else:
            print(f"DEBUG: NO OPPONENT found for week {franchise.current_week} - will show season complete or BYE")
    elif franchise.playoff_state and not franchise.season_complete and not user_team.eliminated:
        # Playoffs - find user's next playoff opponent
        next_opponent = _get_playoff_opponent(franchise, user_team)
        if next_opponent:
            next_opponent_ratings = calculate_team_ratings(next_opponent, games_played)
            next_opponent_stats = calculate_team_stats(next_opponent, games_played)

    # Calculate team stat rankings across entire league
    all_teams = franchise.teams
    stat_rankings = calculate_stat_rankings(user_team, all_teams, games_played)

    # Get last game summary
    last_game_summary = None
    if games_played > 0 and hasattr(user_team, 'last_game_stats'):
        last_game_summary = user_team.last_game_stats

    # Detect BYE week (no opponent but still in regular season)
    is_bye_week = (franchise.current_week <= SEASON_GAMES and
                   not next_opponent and
                   not franchise.playoff_state and
                   not franchise.season_complete)

    # Detect if user is watching playoffs (eliminated or didn't make playoffs, but playoffs ongoing)
    is_watching_playoffs = (franchise.playoff_state and
                           not franchise.season_complete and
                           (user_team.eliminated or not hasattr(user_team, 'playoff_seed') or user_team.playoff_seed is None))

    return render_template('index.html',
                         franchise=franchise,
                         user_team=user_team,
                         ratings=ratings,
                         user_stats=user_stats,
                         div_teams=div_teams,
                         next_opponent=next_opponent,
                         next_opponent_ratings=next_opponent_ratings,
                         next_opponent_stats=next_opponent_stats,
                         games_played=games_played,
                         stat_rankings=stat_rankings,
                         last_game_summary=last_game_summary,
                         is_bye_week=is_bye_week,
                         is_watching_playoffs=is_watching_playoffs)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial franchise setup"""
    if request.method == 'POST':
        team_name = request.form.get('team_name')

        # Create new franchise
        teams = create_new_league()

        # Find the selected team
        selected_team = next((t for t in teams if t.name == team_name), teams[0])

        franchise = Franchise(
            teams=teams,
            user_team_name=selected_team.name,
            current_season=1,
            current_week=1
        )

        # Generate season schedule
        from utils.schedule import generate_season_schedule
        franchise.schedule = generate_season_schedule(teams)

        save_current_franchise(franchise)
        return redirect(url_for('index'))

    # Show team selection
    try:
        teams = create_new_league()
        team_names = sorted([t.name for t in teams])
        print(f"Loaded {len(teams)} teams for selection")  # Debug log

        if not team_names:
            return render_template('setup.html', team_names=[], error="No teams loaded. Check if fake_nfl_rosters.xlsx exists.")

        return render_template('setup.html', team_names=team_names)
    except Exception as e:
        print(f"Error loading teams: {e}")  # Debug log
        import traceback
        traceback.print_exc()
        return render_template('setup.html', team_names=[], error=f"Error loading teams: {str(e)}")


@app.route('/simulate')
def simulate():
    """Simulate game page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))

    user_team = get_user_team(franchise)

    # Determine if this is a playoff game
    is_playoff = franchise.playoff_state is not None and franchise.current_week > SEASON_GAMES

    if is_playoff:
        # Get playoff opponent
        opponent = _get_playoff_opponent(franchise, user_team)
    else:
        # Get opponent from regular season schedule
        from utils.schedule import get_next_opponent as schedule_get_next_opponent
        opponent = schedule_get_next_opponent(franchise, user_team.name)

    if not opponent:
        # No opponent (BYE week or season over) - redirect to home
        return redirect(url_for('index'))

    games_played = franchise.current_week - 1

    # Calculate ratings for both teams
    user_ratings = calculate_team_ratings(user_team, games_played)
    opponent_ratings = calculate_team_ratings(opponent, games_played)

    # Calculate statistics for both teams
    user_stats = calculate_team_stats(user_team, games_played)
    opponent_stats = calculate_team_stats(opponent, games_played)

    # Get top players for both teams
    user_top_players = get_top_players(user_team, games_played)
    opponent_top_players = get_top_players(opponent, games_played)

    # Get team abbreviations
    from config import TEAM_ABBREVIATIONS
    user_abbrev = TEAM_ABBREVIATIONS.get(user_team.name, user_team.name[:3].upper())
    opponent_abbrev = TEAM_ABBREVIATIONS.get(opponent.name, opponent.name[:3].upper())

    return render_template('simulate.html',
                         franchise=franchise,
                         user_team=user_team,
                         opponent=opponent,
                         user_ratings=user_ratings,
                         opponent_ratings=opponent_ratings,
                         user_stats=user_stats,
                         opponent_stats=opponent_stats,
                         user_top_players=user_top_players,
                         opponent_top_players=opponent_top_players,
                         user_abbrev=user_abbrev,
                         opponent_abbrev=opponent_abbrev,
                         is_playoff=is_playoff)


@app.route('/api/simulate-game', methods=['POST'])
def api_simulate_game():
    """API endpoint to run game simulation"""
    franchise = get_franchise()
    if not franchise:
        return jsonify({'error': 'No franchise found'}), 404

    user_team = get_user_team(franchise)
    fast_sim = request.json.get('fast_sim', False) if request.json else False

    # Determine if this is a playoff game
    is_playoff = franchise.playoff_state is not None and franchise.current_week > SEASON_GAMES

    if is_playoff:
        # Playoff game
        opponent = _get_playoff_opponent(franchise, user_team)
        if not opponent:
            return jsonify({'error': 'No playoff opponent found'}), 400

        # Simulate user's playoff game
        winner = simulate_game(user_team, opponent, user_team=user_team.name, is_playoff=True)

        # Get play-by-play (always include plays now)
        plays = user_team.last_game_plays

        # Simulate other playoff games in this round
        other_games = []
        _simulate_playoff_round(franchise, user_team, opponent, other_games)

        # Advance playoff state
        _advance_playoff_bracket(franchise, user_team)

        # Save franchise
        save_current_franchise(franchise)

        return jsonify({
            'plays': plays,
            'user_score': user_team.score,
            'opponent_score': opponent.score,
            'winner': winner.name,
            'current_week': franchise.current_week,
            'other_games': other_games,
            'fast_sim': fast_sim,
            'is_playoff': True,
            'playoff_state': franchise.playoff_state
        })

    else:
        # Regular season game - use schedule
        from utils.schedule import get_next_opponent as schedule_get_next_opponent

        # Get opponent from schedule
        opponent = schedule_get_next_opponent(franchise, user_team.name)

        if not opponent:
            # BYE week - no game to simulate
            franchise.current_week += 1
            save_current_franchise(franchise)
            return jsonify({
                'plays': [f"Week {franchise.current_week - 1} - BYE WEEK", f"{user_team.name} has a bye week this week."],
                'user_score': 0,
                'opponent_score': 0,
                'winner': 'BYE',
                'current_week': franchise.current_week,
                'other_games': [],
                'fast_sim': False,
                'is_playoff': False,
                'is_bye': True
            })

        # Simulate the user's game
        winner = simulate_game(user_team, opponent, user_team=user_team.name, is_playoff=False)

        # Get play-by-play for user's game
        plays = user_team.last_game_plays

        # Update schedule to mark game as played
        if franchise.current_week in franchise.schedule:
            for matchup in franchise.schedule[franchise.current_week]:
                if matchup['home'].name == user_team.name and matchup['away'].name == opponent.name:
                    matchup['played'] = True
                    matchup['home_score'] = user_team.score
                    matchup['away_score'] = opponent.score
                    break
                elif matchup['away'].name == user_team.name and matchup['home'].name == opponent.name:
                    matchup['played'] = True
                    matchup['home_score'] = opponent.score
                    matchup['away_score'] = user_team.score
                    break

        # Simulate all other games in the week from schedule
        other_games = []
        if franchise.current_week in franchise.schedule:
            for matchup in franchise.schedule[franchise.current_week]:
                home = matchup['home']
                away = matchup['away']

                # Skip if already played (user's game)
                if matchup['played']:
                    continue

                # Simulate this game
                game_winner = simulate_game(home, away, user_team=None, is_playoff=False)
                matchup['played'] = True
                matchup['home_score'] = home.score
                matchup['away_score'] = away.score

                other_games.append({
                    'team1': home.name,
                    'team1_score': home.score,
                    'team2': away.name,
                    'team2_score': away.score
                })

        # Advance week
        franchise.current_week += 1

        # Save franchise
        save_current_franchise(franchise)

        return jsonify({
            'plays': plays,
            'user_score': user_team.score,
            'opponent_score': opponent.score,
            'winner': winner.name,
            'current_week': franchise.current_week,
            'other_games': other_games,
            'fast_sim': fast_sim,
            'is_playoff': False
        })


@app.route('/api/simulate-week', methods=['POST'])
def api_simulate_week():
    """API endpoint to simulate all games in the week and advance (used for BYE weeks)"""
    franchise = get_franchise()
    if not franchise:
        return jsonify({'error': 'No franchise found'}), 404

    user_team = get_user_team(franchise)

    # Simulate all games in the current week
    other_games = []
    if franchise.current_week in franchise.schedule:
        for matchup in franchise.schedule[franchise.current_week]:
            home = matchup['home']
            away = matchup['away']

            # Skip if already played
            if matchup['played']:
                continue

            # Simulate this game
            game_winner = simulate_game(home, away, user_team=None, is_playoff=False)
            matchup['played'] = True
            matchup['home_score'] = home.score
            matchup['away_score'] = away.score

            other_games.append({
                'team1': home.name,
                'team1_score': home.score,
                'team2': away.name,
                'team2_score': away.score
            })

    # Advance week
    franchise.current_week += 1

    # Save franchise
    save_current_franchise(franchise)

    return jsonify({
        'success': True,
        'current_week': franchise.current_week,
        'other_games': other_games
    })


@app.route('/api/simulate-playoff-round', methods=['POST'])
def api_simulate_playoff_round():
    """API endpoint to simulate all playoff games in current round (used when eliminated/spectating)"""
    franchise = get_franchise()
    if not franchise:
        return jsonify({'error': 'No franchise found'}), 404

    if not franchise.playoff_state or franchise.season_complete:
        return jsonify({'error': 'No playoff games to simulate'}), 400

    user_team = get_user_team(franchise)
    other_games = []

    # Get all playoff teams
    playoff_teams = [t for t in franchise.teams if hasattr(t, 'playoff_seed') and t.playoff_seed is not None]

    current_round = franchise.playoff_state

    if franchise.playoff_state == 'wildcard':
        # Simulate wild card games
        for conf in ['afc', 'nfc']:
            matchups = franchise.playoff_bracket['wildcard'][conf]
            for matchup in matchups:
                team1 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed1']), None)
                team2 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed2']), None)

                if team1 and team2:
                    winner = simulate_game(team1, team2, user_team=None, is_playoff=True)
                    other_games.append({
                        'team1': team1.name,
                        'team1_score': team1.score,
                        'team2': team2.name,
                        'team2_score': team2.score,
                        'playoff_round': 'Wild Card'
                    })

        # Collect wild card winners
        for conf in ['afc', 'nfc']:
            winners = [t for t in franchise.teams
                      if t.league == conf.upper()
                      and hasattr(t, 'playoff_seed')
                      and t.playoff_seed is not None
                      and not t.eliminated
                      and t.playoff_wins > 0]

            # Add #1 seed (gets bye)
            seed1 = next((t for t in franchise.teams
                         if t.league == conf.upper() and t.playoff_seed == 1), None)
            if seed1 and not seed1.eliminated:
                winners.insert(0, seed1)

            franchise.playoff_bracket['wildcard_winners'][conf] = winners

        # Generate divisional matchups
        for conf in ['afc', 'nfc']:
            winners = franchise.playoff_bracket['wildcard_winners'][conf]
            if len(winners) >= 4:
                seeds = sorted([t.playoff_seed for t in winners])
                franchise.playoff_bracket['divisional'][conf] = [
                    {'seed1': seeds[0], 'seed2': seeds[3]},
                    {'seed1': seeds[1], 'seed2': seeds[2]}
                ]

        franchise.playoff_state = 'divisional'

    elif franchise.playoff_state == 'divisional':
        # Simulate divisional games
        for conf in ['afc', 'nfc']:
            matchups = franchise.playoff_bracket['divisional'][conf]
            for matchup in matchups:
                team1 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed1']), None)
                team2 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed2']), None)

                if team1 and team2 and not team1.eliminated and not team2.eliminated:
                    winner = simulate_game(team1, team2, user_team=None, is_playoff=True)
                    other_games.append({
                        'team1': team1.name,
                        'team1_score': team1.score,
                        'team2': team2.name,
                        'team2_score': team2.score,
                        'playoff_round': 'Divisional'
                    })

        # Collect divisional winners
        for conf in ['afc', 'nfc']:
            winners = [t for t in franchise.teams
                      if t.league == conf.upper()
                      and hasattr(t, 'playoff_seed')
                      and not t.eliminated
                      and t.playoff_wins >= 2]
            franchise.playoff_bracket['divisional_winners'][conf] = winners

        # Generate conference championship matchups
        for conf in ['afc', 'nfc']:
            winners = franchise.playoff_bracket['divisional_winners'][conf]
            if len(winners) >= 2:
                seeds = sorted([t.playoff_seed for t in winners])
                franchise.playoff_bracket['conference'][conf] = [
                    {'seed1': seeds[0], 'seed2': seeds[1]}
                ]

        franchise.playoff_state = 'conference'

    elif franchise.playoff_state == 'conference':
        # Simulate conference championships
        for conf in ['afc', 'nfc']:
            matchups = franchise.playoff_bracket['conference'][conf]
            if matchups:
                matchup = matchups[0]
                team1 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed1']), None)
                team2 = next((t for t in playoff_teams
                            if t.league == conf.upper() and t.playoff_seed == matchup['seed2']), None)

                if team1 and team2 and not team1.eliminated and not team2.eliminated:
                    winner = simulate_game(team1, team2, user_team=None, is_playoff=True)
                    other_games.append({
                        'team1': team1.name,
                        'team1_score': team1.score,
                        'team2': team2.name,
                        'team2_score': team2.score,
                        'playoff_round': 'Conference Championship'
                    })

        # Collect conference champions
        afc_champ = next((t for t in franchise.teams
                         if t.league == 'AFC' and not t.eliminated and t.playoff_wins >= 3), None)
        nfc_champ = next((t for t in franchise.teams
                         if t.league == 'NFC' and not t.eliminated and t.playoff_wins >= 3), None)

        if afc_champ and nfc_champ:
            franchise.playoff_bracket['superbowl'] = [{
                'seed1': afc_champ.playoff_seed,
                'seed2': nfc_champ.playoff_seed,
                'conf1': 'AFC',
                'conf2': 'NFC'
            }]
            franchise.playoff_state = 'superbowl'

    elif franchise.playoff_state == 'superbowl':
        # Simulate Super Bowl
        superbowl = franchise.playoff_bracket['superbowl'][0]
        afc_team = next((t for t in franchise.teams
                        if t.league == 'AFC' and t.playoff_seed == superbowl['seed1']), None)
        nfc_team = next((t for t in franchise.teams
                        if t.league == 'NFC' and t.playoff_seed == superbowl['seed2']), None)

        if afc_team and nfc_team:
            winner = simulate_game(afc_team, nfc_team, user_team=None, is_playoff=True)
            other_games.append({
                'team1': afc_team.name,
                'team1_score': afc_team.score,
                'team2': nfc_team.name,
                'team2_score': nfc_team.score,
                'playoff_round': 'Super Bowl',
                'champion': winner.name
            })

        # Super Bowl complete - season over
        franchise.season_complete = True

    # Save franchise
    save_current_franchise(franchise)

    return jsonify({
        'success': True,
        'playoff_state': franchise.playoff_state,
        'season_complete': franchise.season_complete,
        'games': other_games,
        'previous_round': current_round
    })


@app.route('/standings')
def standings():
    """View league standings"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))

    # Organize teams by division
    standings_data = {}
    for league in ['AFC', 'NFC']:
        standings_data[league] = {}
        for division in ['North', 'South', 'East', 'West']:
            teams = [t for t in franchise.teams if t.league == league and t.division == division]
            teams.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)

            # Calculate games back for each team
            if teams:
                leader_wins = teams[0].wins
                leader_losses = teams[0].losses
                for team in teams:
                    gb = ((leader_wins - team.wins) + (team.losses - leader_losses)) / 2.0
                    team.games_back = gb if gb > 0 else 0

            standings_data[league][division] = teams

    return render_template('standings.html',
                         franchise=franchise,
                         standings=standings_data)


@app.route('/team/<team_name>')
def team_stats(team_name):
    """View detailed team stats"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))

    team = next((t for t in franchise.teams if t.name == team_name), None)
    if not team:
        return redirect(url_for('standings'))

    games_played = franchise.current_week - 1

    # Get top players
    qbs = sorted([p for p in team.qb_starters], key=lambda x: x.pass_yards, reverse=True)
    rbs = sorted([p for p in team.rb_starters], key=lambda x: x.rush_yards, reverse=True)
    receivers = sorted(team.wr_starters + team.te_starters, key=lambda x: x.rec_yards, reverse=True)[:5]
    defenders = sorted(team.defense_starters, key=lambda x: x.tackles, reverse=True)[:5]

    return render_template('team.html',
                         franchise=franchise,
                         team=team,
                         games_played=games_played,
                         qbs=qbs,
                         rbs=rbs,
                         receivers=receivers,
                         defenders=defenders)


@app.route('/playbyplay')
def playbyplay():
    """View last game play-by-play"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))

    user_team = get_user_team(franchise)

    if not hasattr(user_team, 'last_game_plays') or not user_team.last_game_plays:
        plays = ["No game data available yet."]
    else:
        plays = user_team.last_game_plays

    return render_template('playbyplay.html',
                         franchise=franchise,
                         user_team=user_team,
                         plays=plays)


@app.route('/reset')
def reset():
    """Reset franchise (for testing)"""
    if os.path.exists(FRANCHISE_FILE):
        os.remove(FRANCHISE_FILE)
    return redirect(url_for('setup'))


# TEAM Routes
@app.route('/team/roster')
def team_roster():
    """Player list page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))
    user_team = get_user_team(franchise)
    # TODO: Implement player list with sortable table
    return render_template('team_roster.html', franchise=franchise, user_team=user_team)


@app.route('/team/schedule')
def team_schedule():
    """Team schedule page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))
    user_team = get_user_team(franchise)
    # TODO: Implement schedule view
    return render_template('team_schedule.html', franchise=franchise, user_team=user_team)


@app.route('/team/history')
def team_history():
    """Team history page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))
    user_team = get_user_team(franchise)
    # TODO: Implement franchise history
    return render_template('team_history.html', franchise=franchise, user_team=user_team)


# LEAGUE Routes
@app.route('/league/schedule')
def league_schedule():
    """League schedule page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))

    # Get selected week from query parameter, default to current week
    selected_week = request.args.get('week', franchise.current_week, type=int)
    selected_week = max(1, min(17, selected_week))  # Clamp to 1-17

    # Generate matchups for the selected week
    week_games = []
    user_team = get_user_team(franchise)

    # Simple round-robin schedule: each team plays the next team in the list
    # This is a simplified scheduler - in production you'd want a more sophisticated one
    teams = franchise.teams
    num_teams = len(teams)

    # Pair up teams for this week
    for i in range(0, num_teams, 2):
        if i + 1 < num_teams:
            # Determine home/away based on week
            if (selected_week + i) % 2 == 0:
                home_team = teams[i]
                away_team = teams[(i + 1 + selected_week - 1) % num_teams]
            else:
                away_team = teams[i]
                home_team = teams[(i + 1 + selected_week - 1) % num_teams]

            # Check if this game has been played
            is_played = selected_week < franchise.current_week
            is_user_game = (home_team == user_team or away_team == user_team)

            week_games.append({
                'home_team': home_team.name,
                'away_team': away_team.name,
                'home_score': home_team.score if is_played else 0,
                'away_score': away_team.score if is_played else 0,
                'is_played': is_played,
                'is_user_game': is_user_game
            })

    return render_template('league_schedule.html',
                         franchise=franchise,
                         selected_week=selected_week,
                         week_games=week_games)


@app.route('/api/game-stats')
def api_game_stats():
    """API endpoint to get player stats for the LAST GAME ONLY (not season totals)"""
    franchise = get_franchise()
    if not franchise:
        return jsonify({'error': 'No franchise found'}), 404

    team_name = request.args.get('team')
    if not team_name:
        return jsonify({'error': 'Team name required'}), 400

    # Find the team
    team = next((t for t in franchise.teams if t.name == team_name), None)
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    # Use last_game_player_stats (game deltas) instead of season totals
    player_stats = []
    if hasattr(team, 'last_game_player_stats') and team.last_game_player_stats:
        for player_name, game_stats in team.last_game_player_stats.items():
            # Find player to get position
            player = next((p for p in team.players if p.name == player_name), None)
            if not player:
                continue

            # Only include players who had stats in this game
            has_stats = any(game_stats.get(stat, 0) > 0 for stat in game_stats)
            if not has_stats:
                continue

            player_data = {
                'name': player_name,
                'position': player.position,
                'pass_attempts': game_stats.get('pass_attempts', 0),
                'pass_completions': game_stats.get('pass_completions', 0),
                'pass_yards': game_stats.get('pass_yards', 0),
                'pass_td': game_stats.get('pass_td', 0),
                'interceptions': game_stats.get('interceptions', 0),
                'rush_attempts': game_stats.get('rush_attempts', 0),
                'rush_yards': game_stats.get('rush_yards', 0),
                'rush_td': game_stats.get('rush_td', 0),
                'rec_targets': game_stats.get('rec_targets', 0),
                'rec_catches': game_stats.get('rec_catches', 0),
                'rec_yards': game_stats.get('rec_yards', 0),
                'rec_td': game_stats.get('rec_td', 0),
                'tackles': game_stats.get('tackles', 0),
                'sacks': game_stats.get('sacks', 0),
                'interceptions_def': game_stats.get('interceptions_def', 0),
                'pass_deflections': game_stats.get('pass_deflections', 0),
                'forced_fumbles': game_stats.get('forced_fumbles', 0),
                'fg_attempts': game_stats.get('fg_attempts', 0),
                'fg_made': game_stats.get('fg_made', 0),
                'longest_fg': game_stats.get('longest_fg', 0),
                'xp_attempts': game_stats.get('xp_attempts', 0),
                'xp_made': game_stats.get('xp_made', 0),
                'punt_attempts': game_stats.get('punt_attempts', 0),
                'punt_yards': game_stats.get('punt_yards', 0),
                'longest_punt': game_stats.get('longest_punt', 0),
                'inside_20': game_stats.get('inside_20', 0)
            }
            player_stats.append(player_data)

    return jsonify(player_stats)


@app.route('/league/playoffs')
def league_playoffs():
    """Playoffs bracket page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))

    # Check if playoffs have started
    if franchise.current_week <= SEASON_GAMES:
        return render_template('playoffs.html',
                             franchise=franchise,
                             playoffs_started=False,
                             message="Playoffs have not started yet. Complete the regular season first.")

    if not franchise.playoff_state and not franchise.season_complete:
        return render_template('playoffs.html',
                             franchise=franchise,
                             playoffs_started=False,
                             message="Playoffs have not been initialized yet. Please visit the home page.")

    # Get playoff teams with seeds
    playoff_teams = {}
    for conf in ['AFC', 'NFC']:
        conf_teams = [t for t in franchise.teams
                     if t.league == conf
                     and hasattr(t, 'playoff_seed')
                     and t.playoff_seed is not None]
        conf_teams.sort(key=lambda t: t.playoff_seed)
        playoff_teams[conf] = conf_teams

    # Get bracket data
    bracket = franchise.playoff_bracket

    # Helper function to get team by seed
    def get_team_by_seed(conf, seed):
        return next((t for t in franchise.teams
                    if t.league == conf and t.playoff_seed == seed), None)

    return render_template('playoffs.html',
                         franchise=franchise,
                         playoffs_started=True,
                         playoff_teams=playoff_teams,
                         bracket=bracket,
                         playoff_state=franchise.playoff_state,
                         season_complete=franchise.season_complete,
                         get_team_by_seed=get_team_by_seed)


@app.route('/league/stats')
def league_stats():
    """League statistics page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))
    # TODO: Implement league-wide player stats
    return render_template('league_stats.html', franchise=franchise)


@app.route('/league/draft')
def draft_room():
    """Draft room page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))
    # TODO: Implement draft class viewer with scouting
    return render_template('draft_room.html', franchise=franchise)


# SETTINGS Route
@app.route('/settings')
def settings():
    """Settings page"""
    franchise = get_franchise()
    if not franchise:
        return redirect(url_for('setup'))
    # TODO: Implement game settings
    return render_template('settings.html', franchise=franchise)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
