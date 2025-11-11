"""
Flask web application for NFL Football Simulation
"""
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
import pickle
import os
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
            return pickle.load(f)
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
        # Regular season - simple scheduling
        available = [t for t in franchise.teams if t != user_team and t.league == user_team.league]
        if available:
            next_opponent = available[(franchise.current_week - 1) % len(available)]
            next_opponent_ratings = calculate_team_ratings(next_opponent, games_played)
            next_opponent_stats = calculate_team_stats(next_opponent, games_played)
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
                         last_game_summary=last_game_summary)


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

    # Get opponent (simplified - needs proper scheduling)
    available = [t for t in franchise.teams if t != user_team and t.league == user_team.league]
    if not available:
        return redirect(url_for('index'))

    opponent = available[(franchise.current_week - 1) % len(available)]

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

    return render_template('simulate.html',
                         franchise=franchise,
                         user_team=user_team,
                         opponent=opponent,
                         user_ratings=user_ratings,
                         opponent_ratings=opponent_ratings,
                         user_stats=user_stats,
                         opponent_stats=opponent_stats,
                         user_top_players=user_top_players,
                         opponent_top_players=opponent_top_players)


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
        # Regular season game
        available = [t for t in franchise.teams if t != user_team and t.league == user_team.league]
        opponent = available[(franchise.current_week - 1) % len(available)]

        # Simulate the user's game
        winner = simulate_game(user_team, opponent, user_team=user_team.name, is_playoff=False)

        # Get play-by-play for user's game (always include plays now)
        plays = user_team.last_game_plays

        # Simulate all other games in the league for this week
        other_games = []
        simulated_teams = {user_team.name, opponent.name}

        for i in range(0, len(franchise.teams), 2):
            team1 = franchise.teams[i]
            team2 = franchise.teams[i + 1] if i + 1 < len(franchise.teams) else None

            if team2 and team1.name not in simulated_teams and team2.name not in simulated_teams:
                # Simulate this game
                game_winner = simulate_game(team1, team2, user_team=None, is_playoff=False)
                other_games.append({
                    'team1': team1.name,
                    'team1_score': team1.score,
                    'team2': team2.name,
                    'team2_score': team2.score
                })
                simulated_teams.add(team1.name)
                simulated_teams.add(team2.name)

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
