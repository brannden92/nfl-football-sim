"""
Playoff logic for the NFL Football Simulation
"""
from game.simulation import simulate_game


def get_playoff_teams(conference_teams):
    """Get 7 playoff teams from a conference (4 division winners + 3 wild cards)"""
    divisions = {}
    for team in conference_teams:
        if team.division not in divisions:
            divisions[team.division] = []
        divisions[team.division].append(team)

    # Get division winners
    div_winners = []
    for div_teams in divisions.values():
        winner = max(div_teams, key=lambda t: (t.wins, t.points_for - t.points_against))
        div_winners.append(winner)

    # Sort division winners by record
    div_winners.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)

    # Get wild card teams (best non-division winners)
    non_winners = [t for t in conference_teams if t not in div_winners]
    non_winners.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    wild_cards = non_winners[:3]

    # Return all 7 teams seeded by record
    playoff_teams = div_winners + wild_cards
    playoff_teams.sort(key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)

    return playoff_teams


def run_playoffs(franchise):
    """Run playoff bracket with division winners and wild cards"""
    print("\n" + "=" * 70)
    print("PLAYOFFS".center(70))
    print("=" * 70)

    # Get playoff teams for each conference
    afc_teams = get_playoff_teams([t for t in franchise.teams if t.league == "AFC"])
    nfc_teams = get_playoff_teams([t for t in franchise.teams if t.league == "NFC"])

    print("\n=== AFC PLAYOFF TEAMS ===")
    for i, team in enumerate(afc_teams, 1):
        print(f"{i}. {team.name} ({team.wins}-{team.losses})")

    print("\n=== NFC PLAYOFF TEAMS ===")
    for i, team in enumerate(nfc_teams, 1):
        print(f"{i}. {team.name} ({team.wins}-{team.losses})")

    input("\nPress Enter to start Wild Card Round...")

    # Wild Card Round
    print("\n" + "=" * 70)
    print("WILD CARD ROUND".center(70))
    print("=" * 70)

    afc_wc_winners = []
    nfc_wc_winners = []

    # AFC Wild Card (2 vs 7, 3 vs 6, 4 vs 5) - show all playoff scores
    afc_wc_winners.append(simulate_game(afc_teams[1], afc_teams[6], user_team=None))
    afc_wc_winners.append(simulate_game(afc_teams[2], afc_teams[5], user_team=None))
    afc_wc_winners.append(simulate_game(afc_teams[3], afc_teams[4], user_team=None))

    # NFC Wild Card
    nfc_wc_winners.append(simulate_game(nfc_teams[1], nfc_teams[6], user_team=None))
    nfc_wc_winners.append(simulate_game(nfc_teams[2], nfc_teams[5], user_team=None))
    nfc_wc_winners.append(simulate_game(nfc_teams[3], nfc_teams[4], user_team=None))

    input("\nPress Enter to continue to Divisional Round...")

    # Divisional Round
    print("\n" + "=" * 70)
    print("DIVISIONAL ROUND".center(70))
    print("=" * 70)

    # Re-seed winners (1 seed plays lowest remaining seed)
    afc_remaining = [afc_teams[0]] + sorted(
        afc_wc_winners, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True
    )
    nfc_remaining = [nfc_teams[0]] + sorted(
        nfc_wc_winners, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True
    )

    afc_div_winners = []
    nfc_div_winners = []

    afc_div_winners.append(simulate_game(afc_remaining[0], afc_remaining[3], user_team=None))
    afc_div_winners.append(simulate_game(afc_remaining[1], afc_remaining[2], user_team=None))

    nfc_div_winners.append(simulate_game(nfc_remaining[0], nfc_remaining[3], user_team=None))
    nfc_div_winners.append(simulate_game(nfc_remaining[1], nfc_remaining[2], user_team=None))

    input("\nPress Enter to continue to Conference Championships...")

    # Conference Championships
    print("\n" + "=" * 70)
    print("CONFERENCE CHAMPIONSHIPS".center(70))
    print("=" * 70)

    afc_champ = simulate_game(afc_div_winners[0], afc_div_winners[1], user_team=None)
    nfc_champ = simulate_game(nfc_div_winners[0], nfc_div_winners[1], user_team=None)

    input("\nPress Enter to continue to the SUPER BOWL...")

    # Super Bowl
    print("\n" + "=" * 70)
    print("SUPER BOWL".center(70))
    print("=" * 70)

    champion = simulate_game(afc_champ, nfc_champ, user_team=None)

    print("\n" + "=" * 70)
    print(f"🏆 {champion.name} WIN THE SUPER BOWL! 🏆".center(70))
    print("=" * 70)

    return champion
