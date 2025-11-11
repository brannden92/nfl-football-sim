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
    print_team_summary, calculate_team_ratings, view_standings,
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

    # Get division standings
    div_teams = [t for t in franchise.teams if t.league == user_team.league and t.division == user_team.division]
    div_teams.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)

    # Get next opponent
    next_opponent = None
    if franchise.current_week <= SEASON_GAMES:
        # Simple scheduling - would need proper implementation
        available = [t for t in franchise.teams if t != user_team and t.league == user_team.league]
        if available:
            next_opponent = available[franchise.current_week % len(available)]

    return render_template('index.html',
                         franchise=franchise,
                         user_team=user_team,
                         ratings=ratings,
                         div_teams=div_teams,
                         next_opponent=next_opponent,
                         games_played=games_played)


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
    opponent_ratings = calculate_team_ratings(opponent, games_played)

    return render_template('simulate.html',
                         franchise=franchise,
                         user_team=user_team,
                         opponent=opponent,
                         opponent_ratings=opponent_ratings)


@app.route('/api/simulate-game', methods=['POST'])
def api_simulate_game():
    """API endpoint to run game simulation"""
    franchise = get_franchise()
    if not franchise:
        return jsonify({'error': 'No franchise found'}), 404

    user_team = get_user_team(franchise)

    # Get opponent
    available = [t for t in franchise.teams if t != user_team and t.league == user_team.league]
    opponent = available[(franchise.current_week - 1) % len(available)]

    # Simulate the game
    winner = simulate_game(user_team, opponent, user_team=user_team.name)

    # Get play-by-play
    plays = user_team.last_game_plays

    # Advance week
    franchise.current_week += 1

    # Save franchise
    save_current_franchise(franchise)

    return jsonify({
        'plays': plays,
        'user_score': user_team.score,
        'opponent_score': opponent.score,
        'winner': winner.name,
        'current_week': franchise.current_week
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
