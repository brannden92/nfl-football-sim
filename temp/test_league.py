from league import create_nfl_league

teams = create_nfl_league()
print(f"Loaded {len(teams)} teams.")
print("First five teams:")
for t in teams[:5]:
    print("-", t.name, "| Division:", t.division)
