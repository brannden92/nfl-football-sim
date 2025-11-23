from flask import Flask, render_template, request, jsonify
import nfl_data_py as nfl
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Cache for data to avoid excessive API calls
data_cache = {
    'players': None,
    'rosters': None,
    'weekly_stats': None,
    'schedules': None,
    'injuries': None,
    'last_update': None
}

CACHE_DURATION = timedelta(hours=1)

def update_cache():
    """Update the data cache if needed"""
    current_time = datetime.now()

    if data_cache['last_update'] is None or (current_time - data_cache['last_update']) > CACHE_DURATION:
        try:
            print("Updating cache...")
            current_year = datetime.now().year

            # Load player data for current season
            data_cache['players'] = nfl.import_ids()
            data_cache['rosters'] = nfl.import_rosters([current_year])
            data_cache['weekly_stats'] = nfl.import_weekly_data([current_year])
            data_cache['schedules'] = nfl.import_schedules([current_year])

            # Try to get injury data
            try:
                data_cache['injuries'] = nfl.import_injuries([current_year])
            except:
                data_cache['injuries'] = pd.DataFrame()

            data_cache['last_update'] = current_time
            print("Cache updated successfully!")
        except Exception as e:
            print(f"Error updating cache: {e}")
            if data_cache['last_update'] is None:
                # Initialize with empty dataframes if first load fails
                data_cache['players'] = pd.DataFrame()
                data_cache['rosters'] = pd.DataFrame()
                data_cache['weekly_stats'] = pd.DataFrame()
                data_cache['schedules'] = pd.DataFrame()
                data_cache['injuries'] = pd.DataFrame()
                data_cache['last_update'] = current_time

def search_player(player_name):
    """Search for a player by name"""
    update_cache()

    if data_cache['players'].empty:
        return []

    # Search in player IDs database
    players_df = data_cache['players']

    # Case-insensitive search
    mask = players_df['name'].str.contains(player_name, case=False, na=False)
    results = players_df[mask]

    # Get current roster info
    if not data_cache['rosters'].empty:
        current_year = datetime.now().year
        current_rosters = data_cache['rosters'][data_cache['rosters']['season'] == current_year]
        results = results.merge(
            current_rosters[['player_id', 'team', 'position']],
            left_on='gsis_id',
            right_on='player_id',
            how='left'
        )

    return results.to_dict('records')

def get_player_season_stats(player_id):
    """Get player's current season statistics"""
    update_cache()

    if data_cache['weekly_stats'].empty:
        return None

    # Filter for this player
    player_stats = data_cache['weekly_stats'][data_cache['weekly_stats']['player_id'] == player_id]

    if player_stats.empty:
        return None

    # Aggregate season totals
    season_stats = {
        'games_played': len(player_stats),
        'passing_yards': player_stats['passing_yards'].sum() if 'passing_yards' in player_stats else 0,
        'passing_tds': player_stats['passing_tds'].sum() if 'passing_tds' in player_stats else 0,
        'interceptions': player_stats['interceptions'].sum() if 'interceptions' in player_stats else 0,
        'completions': player_stats['completions'].sum() if 'completions' in player_stats else 0,
        'attempts': player_stats['attempts'].sum() if 'attempts' in player_stats else 0,
        'rushing_yards': player_stats['rushing_yards'].sum() if 'rushing_yards' in player_stats else 0,
        'rushing_tds': player_stats['rushing_tds'].sum() if 'rushing_tds' in player_stats else 0,
        'carries': player_stats['carries'].sum() if 'carries' in player_stats else 0,
        'receptions': player_stats['receptions'].sum() if 'receptions' in player_stats else 0,
        'receiving_yards': player_stats['receiving_yards'].sum() if 'receiving_yards' in player_stats else 0,
        'receiving_tds': player_stats['receiving_tds'].sum() if 'receiving_tds' in player_stats else 0,
        'targets': player_stats['targets'].sum() if 'targets' in player_stats else 0,
        'fantasy_points': player_stats['fantasy_points'].sum() if 'fantasy_points' in player_stats else 0,
        'fantasy_points_ppr': player_stats['fantasy_points_ppr'].sum() if 'fantasy_points_ppr' in player_stats else 0,
    }

    return season_stats

def get_player_game_log(player_id):
    """Get player's current season game log"""
    update_cache()

    if data_cache['weekly_stats'].empty:
        return []

    # Filter for this player and sort by week
    player_stats = data_cache['weekly_stats'][data_cache['weekly_stats']['player_id'] == player_id].copy()
    player_stats = player_stats.sort_values('week', ascending=False)

    # Select relevant columns for display
    columns_to_show = [
        'week', 'opponent_team', 'passing_yards', 'passing_tds', 'interceptions',
        'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards', 'receiving_tds',
        'fantasy_points_ppr'
    ]

    # Only keep columns that exist
    available_columns = [col for col in columns_to_show if col in player_stats.columns]
    game_log = player_stats[available_columns].fillna(0)

    return game_log.to_dict('records')

def get_next_opponent(team_abbr):
    """Get next opponent for a team"""
    update_cache()

    if data_cache['schedules'].empty:
        return None

    current_year = datetime.now().year
    schedules = data_cache['schedules']

    # Get current week (approximate based on date)
    current_date = datetime.now()
    season_start = datetime(current_year, 9, 1)

    if current_date < season_start:
        current_week = 1
    else:
        weeks_since_start = (current_date - season_start).days // 7
        current_week = min(weeks_since_start + 1, 18)

    # Find next game for this team
    team_schedule = schedules[
        ((schedules['home_team'] == team_abbr) | (schedules['away_team'] == team_abbr)) &
        (schedules['week'] >= current_week)
    ].sort_values('week')

    if team_schedule.empty:
        return None

    next_game = team_schedule.iloc[0]

    # Determine opponent
    if next_game['home_team'] == team_abbr:
        opponent = next_game['away_team']
        location = 'vs'
    else:
        opponent = next_game['home_team']
        location = '@'

    return {
        'opponent': opponent,
        'week': next_game['week'],
        'location': location,
        'game_date': next_game.get('gameday', 'TBD'),
        'stadium': next_game.get('stadium', 'TBD')
    }

def get_team_defensive_stats(team_abbr):
    """Get defensive statistics for a team"""
    update_cache()

    if data_cache['weekly_stats'].empty:
        return None

    # Get all opponent stats against this team
    weekly_data = data_cache['weekly_stats']

    # Filter games where opponents played against this team
    team_opponents = weekly_data[weekly_data['opponent_team'] == team_abbr]

    if team_opponents.empty:
        return {
            'points_allowed': 0,
            'yards_allowed': 0,
            'passing_yards_allowed': 0,
            'rushing_yards_allowed': 0,
            'sacks': 0,
            'interceptions': 0,
            'games_played': 0
        }

    # Aggregate defensive stats
    games_played = len(team_opponents['week'].unique())

    defensive_stats = {
        'points_allowed': team_opponents['fantasy_points'].sum() / games_played if games_played > 0 else 0,
        'yards_allowed': (team_opponents['passing_yards'].sum() + team_opponents['rushing_yards'].sum()) / games_played if games_played > 0 else 0,
        'passing_yards_allowed': team_opponents['passing_yards'].sum() / games_played if games_played > 0 else 0,
        'rushing_yards_allowed': team_opponents['rushing_yards'].sum() / games_played if games_played > 0 else 0,
        'games_played': games_played
    }

    return defensive_stats

def get_team_injuries(team_abbr):
    """Get injury report for a team's defense"""
    update_cache()

    if data_cache['injuries'].empty:
        return []

    # Filter for this team's injured players
    team_injuries = data_cache['injuries'][
        (data_cache['injuries']['team'] == team_abbr) &
        (data_cache['injuries']['position'].isin(['DE', 'DT', 'LB', 'CB', 'S', 'DB', 'DL']))
    ]

    if team_injuries.empty:
        return []

    # Get latest injury report
    latest_week = team_injuries['week'].max()
    current_injuries = team_injuries[team_injuries['week'] == latest_week]

    injuries = []
    for _, injury in current_injuries.iterrows():
        injuries.append({
            'player_name': injury.get('full_name', 'Unknown'),
            'position': injury.get('position', 'DEF'),
            'injury_status': injury.get('report_status', 'Unknown')
        })

    return injuries

def get_weather_forecast(city, game_date):
    """Get weather forecast for game location"""
    api_key = os.getenv('WEATHER_API_KEY')

    if not api_key:
        return {
            'temp': 'N/A',
            'condition': 'Weather API key not configured',
            'wind_speed': 'N/A',
            'precipitation': 'N/A'
        }

    try:
        # Use weatherapi.com for forecast
        url = f"http://api.weatherapi.com/v1/forecast.json"
        params = {
            'key': api_key,
            'q': city,
            'days': 7,
            'aqi': 'no',
            'alerts': 'no'
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Try to find forecast for game date
            forecast_day = None
            if 'forecast' in data and 'forecastday' in data['forecast']:
                for day in data['forecast']['forecastday']:
                    if day['date'] == game_date:
                        forecast_day = day
                        break

                # If specific date not found, use first available forecast
                if not forecast_day and len(data['forecast']['forecastday']) > 0:
                    forecast_day = data['forecast']['forecastday'][0]

            if forecast_day:
                return {
                    'temp': f"{forecast_day['day']['avgtemp_f']}°F",
                    'condition': forecast_day['day']['condition']['text'],
                    'wind_speed': f"{forecast_day['day']['maxwind_mph']} mph",
                    'precipitation': f"{forecast_day['day']['daily_chance_of_rain']}% chance"
                }

        return {
            'temp': 'N/A',
            'condition': 'Forecast unavailable',
            'wind_speed': 'N/A',
            'precipitation': 'N/A'
        }

    except Exception as e:
        print(f"Weather API error: {e}")
        return {
            'temp': 'N/A',
            'condition': 'Error fetching weather',
            'wind_speed': 'N/A',
            'precipitation': 'N/A'
        }

# Stadium locations mapping
STADIUM_CITIES = {
    'Arrowhead Stadium': 'Kansas City, MO',
    'Lambeau Field': 'Green Bay, WI',
    'Soldier Field': 'Chicago, IL',
    'MetLife Stadium': 'East Rutherford, NJ',
    'Gillette Stadium': 'Foxborough, MA',
    'Highmark Stadium': 'Buffalo, NY',
    'Hard Rock Stadium': 'Miami, FL',
    'M&T Bank Stadium': 'Baltimore, MD',
    'Paycor Stadium': 'Cincinnati, OH',
    'FirstEnergy Stadium': 'Cleveland, OH',
    'Acrisure Stadium': 'Pittsburgh, PA',
    'NRG Stadium': 'Houston, TX',
    'Lucas Oil Stadium': 'Indianapolis, IN',
    'TIAA Bank Field': 'Jacksonville, FL',
    'Nissan Stadium': 'Nashville, TN',
    'Empower Field at Mile High': 'Denver, CO',
    'Allegiant Stadium': 'Las Vegas, NV',
    'SoFi Stadium': 'Los Angeles, CA',
    'Levi\'s Stadium': 'Santa Clara, CA',
    'Lumen Field': 'Seattle, WA',
    'AT&T Stadium': 'Arlington, TX',
    'Lincoln Financial Field': 'Philadelphia, PA',
    'FedExField': 'Landover, MD',
    'Ford Field': 'Detroit, MI',
    'U.S. Bank Stadium': 'Minneapolis, MN',
    'Mercedes-Benz Stadium': 'Atlanta, GA',
    'Bank of America Stadium': 'Charlotte, NC',
    'Caesars Superdome': 'New Orleans, LA',
    'Raymond James Stadium': 'Tampa, FL',
    'State Farm Stadium': 'Glendale, AZ'
}

@app.route('/')
def index():
    """Home page with search"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Search for a player"""
    data = request.get_json()
    player_name = data.get('player_name', '')

    if not player_name:
        return jsonify({'error': 'Player name required'}), 400

    results = search_player(player_name)

    return jsonify({
        'players': results[:10]  # Limit to 10 results
    })

@app.route('/player/<player_id>')
def player_profile(player_id):
    """Get comprehensive player profile"""
    update_cache()

    # Get player info
    player_info = data_cache['players'][data_cache['players']['gsis_id'] == player_id]

    if player_info.empty:
        return jsonify({'error': 'Player not found'}), 404

    player_info = player_info.iloc[0]

    # Get current team
    current_year = datetime.now().year
    roster_info = data_cache['rosters'][
        (data_cache['rosters']['player_id'] == player_id) &
        (data_cache['rosters']['season'] == current_year)
    ]

    team = roster_info.iloc[0]['team'] if not roster_info.empty else 'N/A'
    position = roster_info.iloc[0]['position'] if not roster_info.empty else 'N/A'

    # Get season stats
    season_stats = get_player_season_stats(player_id)

    # Get game log
    game_log = get_player_game_log(player_id)

    # Get next opponent info
    opponent_info = None
    defensive_stats = None
    injuries = []
    weather = None

    if team != 'N/A':
        opponent_info = get_next_opponent(team)

        if opponent_info:
            defensive_stats = get_team_defensive_stats(opponent_info['opponent'])
            injuries = get_team_injuries(opponent_info['opponent'])

            # Get weather if we have stadium info
            if opponent_info.get('stadium'):
                city = STADIUM_CITIES.get(opponent_info['stadium'], 'New York')
                weather = get_weather_forecast(city, opponent_info.get('game_date', ''))

    return jsonify({
        'player': {
            'name': player_info.get('name', 'Unknown'),
            'team': team,
            'position': position,
            'player_id': player_id
        },
        'season_stats': season_stats,
        'game_log': game_log,
        'opponent_info': opponent_info,
        'defensive_stats': defensive_stats,
        'injuries': injuries,
        'weather': weather
    })

if __name__ == '__main__':
    # Initialize cache on startup
    update_cache()
    app.run(debug=True, host='0.0.0.0', port=5000)
