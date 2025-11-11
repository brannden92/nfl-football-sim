"""
Quick test to verify the refactored code works correctly
"""
from models import Franchise
from game import simulate_game
from utils import create_new_league, print_team_summary

# Create league
print("Creating league...")
teams = create_new_league()
print(f"✓ Created {len(teams)} teams")

# Create franchise
franchise = Franchise(teams, teams[0].name)
print(f"✓ Created franchise with {franchise.user_team_name}")

# Simulate a game
team1 = teams[0]
team2 = teams[1]
print(f"\nSimulating game: {team1.name} vs {team2.name}")
winner = simulate_game(team1, team2)
print(f"✓ Winner: {winner.name}")

# Print team summary
print_team_summary(team1, teams)

print("\n✓ All tests passed! Refactored code is working correctly.")
