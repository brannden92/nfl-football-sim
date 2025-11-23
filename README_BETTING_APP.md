# NFL Player Stats & Betting Analyzer

A Flask web application designed to help with NFL betting decisions by providing comprehensive player statistics, upcoming matchup analysis, and situational information.

## Features

- **Player Search**: Search any NFL player by name
- **Season Statistics**: Complete 2024 season stats for quarterbacks, running backs, receivers, and tight ends
- **Career Game Log**: Week-by-week performance breakdown for the entire season
- **Live Betting Odds**: Real-time player props from major sportsbooks
  - Passing yards Over/Under
  - Rushing yards Over/Under
  - Receiving yards Over/Under
  - Touchdown scorer odds
  - Compare odds across DraftKings, FanDuel, and more
- **Opponent Analysis**:
  - Defensive statistics for upcoming opponent
  - Injured defensive players report
  - Weather forecast for game day
- **Betting Insights**: Automated analysis highlighting favorable/unfavorable matchups
- **Fantasy Points**: PPR fantasy scoring included for all players

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure Environment Variables**

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys (all optional but recommended):

```
WEATHER_API_KEY=your_weather_api_key_here
ODDS_API_KEY=your_odds_api_key_here
```

**API Key Sources:**
- Weather API (free tier): https://www.weatherapi.com/signup.aspx
- The Odds API (500 requests/month free): https://the-odds-api.com/

**Note**: The app works without API keys, but you'll get limited functionality. Betting odds are highly recommended for serious betting analysis!

3. **Run the Application**

```bash
python app.py
```

4. **Access the App**

Open your browser and navigate to:
```
http://localhost:5000
```

## Usage Guide

### Searching for a Player

1. Enter a player's name in the search box (e.g., "Patrick Mahomes", "Josh Allen")
2. Click Search or press Enter
3. Select the desired player from the search results

### Understanding the Data

#### Season Statistics
- Shows cumulative stats for the 2024 season
- Stats displayed vary by position (QB, RB, WR, TE)
- Fantasy points calculated using PPR scoring

#### Matchup Analysis
- **Opponent Info**: Next opponent, game location, and date
- **Defensive Stats**: How the opponent's defense performs against offensive players
- **Injuries**: Defensive players listed on injury report (Out, Questionable, Doubtful)
- **Weather**: Forecasted conditions for game day

#### Live Betting Odds
- **Player Props**: Real-time odds from multiple sportsbooks
- **Market Types**: Passing yards, rushing yards, receiving yards, touchdowns
- **Sportsbook Comparison**: See odds from DraftKings, FanDuel, BetMGM, Caesars, and more
- **Line Shopping**: Compare lines and odds to find the best value

#### Game Log
- Week-by-week breakdown of all 2024 games
- Includes passing, rushing, and receiving stats
- Fantasy points for each game

#### Betting Insights
Automated analysis highlighting:
- Player trending up or down based on recent performance
- Favorable/tough matchups based on opponent defense
- Weather impacts (rain, snow, wind)
- Injury advantages

## Data Sources

This application uses:

- **nfl_data_py**: Official NFL statistics (free, no API key required)
- **The Odds API**: Live betting odds and player props (500 requests/month free)
- **WeatherAPI**: Weather forecasts (free tier available)

Data is cached to minimize API calls and improve performance:
- NFL stats: 1 hour cache
- Betting odds: 15 minute cache (odds change frequently)
- Weather: Included in matchup data cache

## Technical Details

### Architecture

```
nfl-football-sim/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
├── templates/
│   ├── base.html         # Base template
│   └── index.html        # Main page with search and player display
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── main.js       # JavaScript functionality
```

### API Endpoints

- `GET /` - Home page
- `POST /search` - Search for players
  - Body: `{"player_name": "Patrick Mahomes"}`
  - Returns: List of matching players

- `GET /player/<player_id>` - Get player profile
  - Returns: Complete player data including stats, game log, matchup info

### Data Caching

- Player data, rosters, and stats are cached for 1 hour
- Reduces API calls and improves performance
- Cache automatically refreshes after expiration

## Customization

### Changing Cache Duration

Edit `CACHE_DURATION` in `app.py`:

```python
CACHE_DURATION = timedelta(hours=1)  # Change to desired duration
```

### Adding More Stadium Locations

Update the `STADIUM_CITIES` dictionary in `app.py`:

```python
STADIUM_CITIES = {
    'Stadium Name': 'City, State',
    # Add more stadiums...
}
```

### Styling

Modify `static/css/style.css` to customize:
- Colors (see CSS variables at top of file)
- Layout and spacing
- Font sizes and styles

## Troubleshooting

### No Data Loading

**Issue**: Player search returns no results or stats don't load

**Solutions**:
1. Check internet connection
2. Verify `nfl_data_py` is installed: `pip install nfl_data_py`
3. Wait for initial data load (first run may take 30-60 seconds)
4. Check console for error messages

### Weather Not Displaying

**Issue**: Weather section shows "N/A" or errors

**Solutions**:
1. Verify WEATHER_API_KEY is set in `.env` file
2. Check API key is valid at weatherapi.com
3. Ensure you haven't exceeded free tier limits (1M calls/month)

### Slow Performance

**Solutions**:
1. Data cache may need to update - wait 1-2 minutes
2. Clear browser cache
3. Restart the Flask application

### Player Not Found

**Issue**: Can't find a specific player

**Possible reasons**:
1. Player might not be on active roster
2. Try different name format (e.g., "Pat Mahomes" vs "Patrick Mahomes")
3. Check spelling
4. Practice squad players may not be included

## Important Notes

### Responsible Gambling

This tool is for **entertainment and informational purposes only**. Please gamble responsibly:
- Never bet more than you can afford to lose
- Gambling should be for entertainment, not income
- Seek help if gambling becomes a problem: 1-800-GAMBLER

### Data Accuracy

- Stats update throughout the NFL season
- Data is sourced from nfl_data_py (official NFL stats)
- Weather forecasts are predictions and subject to change
- Injury reports may not reflect latest updates (check official sources)

### Legal Disclaimer

This application does not:
- Place bets
- Accept money
- Guarantee outcomes
- Provide professional gambling advice

Always verify information with official NFL sources before making betting decisions.

## Development

### Running in Debug Mode

```bash
export FLASK_ENV=development
python app.py
```

### Adding New Features

The codebase is modular and easy to extend:

1. **New API Endpoints**: Add routes in `app.py`
2. **UI Components**: Modify `templates/index.html`
3. **Styling**: Update `static/css/style.css`
4. **Data Sources**: Add new functions in `app.py`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review error messages in browser console (F12)
3. Check Flask application logs in terminal

## License

This project is for educational and entertainment purposes.

## Credits

Built with:
- Flask (Python web framework)
- nfl_data_py (NFL statistics)
- WeatherAPI (Weather forecasts)

---

**Remember**: This tool provides information to help inform decisions, but sports betting involves risk. Always bet responsibly and within your means.
