# Quick Start Guide - NFL Betting Analyzer

Get up and running in 5 minutes!

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set Up Weather API

For weather forecasts, get a free API key:

1. Visit: https://www.weatherapi.com/signup.aspx
2. Sign up for a free account
3. Copy your API key
4. Edit `.env` file and add your key:

```
WEATHER_API_KEY=your_key_here
```

**Note**: The app works without weather - this is optional!

### 3. Run the App

```bash
python app.py
```

### 4. Open Your Browser

Go to: **http://localhost:5000**

## How to Use

### Search for a Player

1. Type a player name (e.g., "Josh Allen", "Christian McCaffrey")
2. Press Enter or click Search
3. Click on the player from results

### What You'll See

- **Season Stats**: Complete 2024 statistics
- **Next Matchup**: Upcoming opponent with defensive stats
- **Injuries**: Defensive players on injury report
- **Weather**: Game day forecast (if API key configured)
- **Game Log**: Week-by-week performance
- **Betting Insights**: Automated analysis

## Example Players to Search

Try these popular players:

- **Quarterbacks**: Patrick Mahomes, Josh Allen, Lamar Jackson
- **Running Backs**: Christian McCaffrey, Derrick Henry, Saquon Barkley
- **Wide Receivers**: Tyreek Hill, Stefon Diggs, Justin Jefferson
- **Tight Ends**: Travis Kelce, Mark Andrews, George Kittle

## Troubleshooting

### No Results Found?

- Check your internet connection
- Wait 30-60 seconds on first load (data is downloading)
- Try a different spelling of the name

### Weather Not Showing?

- Weather requires WEATHER_API_KEY in .env
- Get free key at: https://www.weatherapi.com/signup.aspx
- The app still works without weather data!

### Slow Loading?

- First load downloads NFL data (takes 1-2 minutes)
- Data is cached for 1 hour after that
- Subsequent searches are much faster

## What Makes a Good Bet?

Look for these indicators:

✅ **Good Signs**:
- Player trending UP in recent games
- Opponent allows high fantasy points
- Key defensive players injured/out
- Good weather conditions (for passing)

⚠️ **Warning Signs**:
- Player trending DOWN
- Opponent has strong defense
- Bad weather (rain, wind for passing)
- Multiple defensive starters healthy

## Important Notes

### Data Freshness

- Stats update throughout the season
- Cache refreshes every hour
- Injury reports may lag by a day

### Responsible Gambling

- This is for entertainment only
- Never bet more than you can afford
- Always verify data with official sources
- Call 1-800-GAMBLER if you need help

## Next Steps

- Read full documentation: `README_BETTING_APP.md`
- Customize styling in: `static/css/style.css`
- Explore code in: `app.py`

## Support

If you encounter issues:

1. Check error messages in browser console (F12)
2. Check terminal where Flask is running
3. Review `README_BETTING_APP.md` troubleshooting section

---

**Ready to analyze some NFL matchups? Start searching! 🏈**
