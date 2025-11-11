"""
Data loading utilities for the NFL Football Simulation
"""
import pandas as pd
from models import Player, Team


def load_rosters_from_excel(filename="fake_nfl_rosters.xlsx"):
    """Load player rosters from Excel file"""
    df = pd.read_excel(filename)
    df.columns = df.columns.str.strip()  # remove extra spaces

    teams = {}
    for _, row in df.iterrows():
        player = Player(
            name=row["Player Name"],
            position=row["Position"],
            skill=row["Skill"],
            age=row["Age"],
        )
        # Optional attributes
        player.durability = row.get("Durability", 100)
        player.starter_rank = row.get("Starter Rank", 1)

        team_name = row["Team"]
        if team_name not in teams:
            teams[team_name] = []
        teams[team_name].append(player)

    return teams  # dict: {team_name: [Player, Player, ...]}


def create_new_league():
    """Create a new league with all NFL teams"""
    team_names = [
        "Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets",
        "Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers",
        "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans",
        "Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
        "Dallas Cowboys", "New York Giants", "Philadelphia Eagles", "Washington Commanders",
        "Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings",
        "Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers",
        "Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks"
    ]

    leagues = {
        "AFC": {"East": [], "North": [], "South": [], "West": []},
        "NFC": {"East": [], "North": [], "South": [], "West": []}
    }

    # Load rosters from Excel
    rosters = load_rosters_from_excel("fake_nfl_rosters.xlsx")

    idx = 0
    for league_name, divs in leagues.items():
        for div_name in divs:
            for _ in range(4):
                team = Team(team_names[idx])
                team.players = rosters.get(team.name, [])
                team.qb_starters = [p for p in team.players if p.position == "QB"][:1]
                team.rb_starters = [p for p in team.players if p.position == "RB"][:2]
                team.wr_starters = [p for p in team.players if p.position == "WR"][:2]
                team.te_starters = [p for p in team.players if p.position == "TE"][:2]
                team.defense_starters = [p for p in team.players if p.position in ["DL", "LB", "CB", "S"]]
                team.league = league_name
                team.division = div_name
                leagues[league_name][div_name].append(team)
                idx += 1

    teams = [t for l in leagues.values() for d in l.values() for t in d]
    return teams
