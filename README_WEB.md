# NFL Football Simulation - Web Interface

A Flask-based web interface for the NFL Football Simulation game, inspired by Out Of The Park Baseball's UI design.

## Features

### Current Pages
- **Dashboard** - Season overview, team stats, division standings
- **Simulate Game** - Live play-by-play with real-time score updates
- **Standings** - Full league standings (AFC/NFC divisions)
- **Team Stats** - Detailed player statistics for any team
- **Play-by-Play** - Review last game's complete play-by-play

### Key Features
- ✅ Clean, responsive Bootstrap 5 UI
- ✅ Real-time game simulation with streaming play-by-play
- ✅ Interactive team ratings with progress bars
- ✅ Division standings with clickable teams
- ✅ Detailed player statistics tables
- ✅ Season tracking (Week/Season display)

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements-web.txt
```

2. **Run the Flask app:**
```bash
python app.py
```

3. **Open your browser:**
Navigate to `http://localhost:5000`

## How to Use

### First Time Setup
1. Visit `http://localhost:5000`
2. Select your team from the dropdown
3. Click "Start Franchise"

### Playing the Game
1. **Dashboard** - View your team's current record and next opponent
2. **Simulate Game** - Click to watch the live play-by-play simulation
3. **View Results** - Check standings, stats, and play-by-play after each game
4. **Continue Season** - Return to dashboard to play the next week

### Navigation
- **Dashboard** - Home page with overview
- **Simulate Game** - Run the next game
- **Standings** - View all teams in the league
- **Play-by-Play** - Review your last game in detail

## Project Structure

```
nfl-football-sim/
├── app.py                 # Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Dashboard
│   ├── setup.html        # Initial team selection
│   ├── simulate.html     # Game simulation
│   ├── standings.html    # League standings
│   ├── team.html         # Team stats
│   └── playbyplay.html   # Play-by-play viewer
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/               # JavaScript files
├── models/               # Game logic (existing)
├── game/                 # Simulation engine (existing)
└── utils/                # Helper functions (existing)
```

## Features Breakdown

### Dashboard (`/`)
- Team record and stats
- Team ratings (Pass/Rush Offense, Pass/Rush Defense)
- Division standings
- Next opponent preview
- Quick link to simulate next game

### Game Simulation (`/simulate`)
- Opponent preview with ratings
- Live play-by-play updates
- Real-time score tracking
- Automatic play streaming (200ms per play)
- Game summary at completion

### Standings (`/standings`)
- All 8 divisions (AFC/NFC × 4 divisions)
- Win/Loss records
- Points For/Against
- Point differential
- Clickable teams to view stats

### Team Stats (`/team/<name>`)
- Team season overview
- QB passing stats
- RB rushing stats
- Receiver stats
- Defensive leaders

## API Endpoints

- `POST /api/simulate-game` - Simulates a game and returns play-by-play
  - Returns: `{plays, user_score, opponent_score, winner, current_week}`

## Future Enhancements

### Potential Additions
- [ ] Draft screen with interactive draft board
- [ ] Scouting interface
- [ ] Roster management (depth chart editing)
- [ ] Player cards with detailed attributes
- [ ] Career stats viewer
- [ ] Playoff bracket visualization
- [ ] Trade screen
- [ ] Free agency
- [ ] Game settings/options
- [ ] Multiple franchise save slots
- [ ] Database persistence (SQLite/PostgreSQL)
- [ ] User authentication
- [ ] WebSocket support for real-time multiplayer

## Development

### Running in Development
```bash
python app.py
```
The app runs on `http://0.0.0.0:5000` with debug mode enabled.

### Data Persistence
Currently uses pickle file (`web_franchise.pkl`) for saving franchise state. For production, consider migrating to a database.

### Reset Franchise
Visit `http://localhost:5000/reset` to clear and restart the franchise.

## Technologies Used
- **Backend:** Flask 3.0
- **Frontend:** Bootstrap 5.3, Vanilla JavaScript
- **Data:** Pandas, Pickle
- **Game Engine:** Custom Python simulation (see main README)

## Notes
- The web interface uses the same backend logic as the CLI version
- All game simulation happens server-side
- Play-by-play streams to browser using JavaScript intervals
- No database required (currently file-based storage)

## Troubleshooting

**Port already in use:**
```bash
# Change port in app.py or kill the process
lsof -ti:5000 | xargs kill -9
```

**Missing dependencies:**
```bash
pip install -r requirements-web.txt
```

**Franchise data corrupted:**
```bash
# Delete the franchise file
rm web_franchise.pkl
```

## Credits
Inspired by Out Of The Park Baseball's excellent UI design.
