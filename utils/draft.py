"""
Draft and scouting system for the NFL Football Simulation
"""
import random
from prettytable import PrettyTable
from models import Player


def get_team_emoji(league, division):
    """Return emoji for team based on league and division"""
    emojis = {
        ('AFC', 'North'): '🦅', ('AFC', 'South'): '🐎',
        ('AFC', 'East'): '🐬', ('AFC', 'West'): '🏈',
        ('NFC', 'North'): '🐻', ('NFC', 'South'): '🐆',
        ('NFC', 'East'): '⭐', ('NFC', 'West'): '🌊'
    }
    return emojis.get((league, division), '🏈')


def get_scout_indicator(scout_points):
    """Return indicator showing scouting investment level"""
    if scout_points == 0:
        return "?"
    elif scout_points == 1:
        return "•"
    elif scout_points == 2:
        return "••"
    else:
        return "•••"


def generate_draft_prospects(num_prospects=350):
    """Generate draft prospects with varying skills and positions"""
    prospects = []
    positions = ['QB', 'RB', 'WR', 'TE', 'OL', 'DEF']
    position_weights = [0.08, 0.18, 0.22, 0.08, 0.14, 0.30]  # Include OL prospects

    first_names = [
        "James", "John", "Michael", "David", "Chris", "Matt", "Josh", "Tom",
        "Aaron", "Patrick", "Russell", "Derek", "Justin", "Lamar", "Dak",
        "Kirk", "Ryan", "Baker", "Sam", "Daniel", "Jared", "Carson", "Drew",
        "Ben", "Philip", "Eli", "Joe", "Cam", "Tyrod", "Teddy", "Marcus",
        "Jameis", "Gardner", "Nick", "Case", "Mitchell", "Tua", "Trevor",
        "Zach", "Mac", "Davis", "Jalen", "Kenny", "Desmond", "CJ", "Bryce"
    ]

    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
        "Lee", "Thompson", "White", "Harris", "Clark", "Lewis", "Robinson",
        "Walker", "Young", "Allen", "King", "Wright", "Hill", "Scott", "Green",
        "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Roberts"
    ]

    for i in range(num_prospects):
        position = random.choices(positions, weights=position_weights)[0]
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = 21  # Draft prospects are typically 21

        # Generate skill with bell curve distribution (more average players)
        base_skill = int(random.gauss(68, 12))
        skill = max(45, min(95, base_skill))

        # Create player with is_draft_prospect=True
        player = Player(name, position, skill, age, is_draft_prospect=True)
        prospects.append(player)

    return prospects


def calculate_draft_order(teams):
    """Calculate draft order based on inverse standings (worst team picks first)"""
    # Sort teams by wins (ascending), then by point differential (ascending)
    sorted_teams = sorted(
        teams,
        key=lambda t: (t.wins, t.points_for - t.points_against)
    )
    return sorted_teams


def view_draft_prospects(franchise, position_filter=None, min_overall=0):
    """Display draft prospects with scouting information"""
    prospects = franchise.draft_prospects

    if not prospects:
        print("\nNo draft prospects available.")
        return

    # Filter by position if specified
    if position_filter:
        prospects = [p for p in prospects if p.position == position_filter]

    # Filter by minimum overall
    if min_overall > 0:
        prospects = [p for p in prospects if p.get_overall_potential() >= min_overall]

    print(f"\n{'=' * 100}")
    print(f"DRAFT PROSPECTS (Scouting Points Available: {franchise.scouting_points})".center(100))
    print(f"{'=' * 100}")

    table = PrettyTable()
    table.field_names = ["#", "Name", "Pos", "Age", "Overall", "Speed", "Str", "Potential", "Scout"]
    table.align["Name"] = "l"

    # Sort by overall rating (higher is better)
    prospects_sorted = sorted(
        prospects,
        key=lambda p: p.skill,
        reverse=True
    )

    for idx, prospect in enumerate(prospects_sorted[:50], 1):  # Show top 50
        scout_points = franchise.scouting_investment.get(prospect.name, 0)
        scout_indicator = get_scout_indicator(scout_points)

        # Get scouted ratings
        speed_rating = prospect.get_draft_rating('speed', scout_points)
        strength_rating = prospect.get_draft_rating('strength', scout_points)
        overall_potential = int(prospect.get_overall_potential())

        table.add_row([
            idx,
            prospect.name[:20],
            prospect.position,
            prospect.age,
            prospect.skill,
            speed_rating,
            strength_rating,
            overall_potential,
            scout_indicator
        ])

    print(table)
    print(f"\nScout Legend: ? = Not scouted, • = 1 pt, •• = 2 pts, ••• = 3 pts (max)")
    print(f"Showing top 50 prospects. Total prospects: {len(prospects)}")


def run_scouting(franchise):
    """Scouting interface - invest points to get better info on prospects"""
    while True:
        print(f"\n{'=' * 70}")
        print(f"SCOUTING DEPARTMENT".center(70))
        print(f"{'=' * 70}")
        print(f"Scouting Points Available: {franchise.scouting_points}")
        print("\n1. View All Prospects")
        print("2. Filter by Position (QB/RB/WR/TE/DEF)")
        print("3. Scout a Player (costs 1-3 points)")
        print("4. View Top Prospects")
        print("5. Exit Scouting")

        choice = input("> ").strip()

        if choice == "1":
            view_draft_prospects(franchise)

        elif choice == "2":
            print("\nSelect Position:")
            print("1. QB  2. RB  3. WR  4. TE  5. DEF")
            pos_choice = input("> ").strip()
            pos_map = {"1": "QB", "2": "RB", "3": "WR", "4": "TE", "5": "DEF"}
            if pos_choice in pos_map:
                view_draft_prospects(franchise, position_filter=pos_map[pos_choice])

        elif choice == "3":
            view_draft_prospects(franchise)
            print("\nEnter player name to scout (or 'back' to cancel):")
            player_name = input("> ").strip()

            if player_name.lower() == 'back':
                continue

            # Find player
            prospect = next((p for p in franchise.draft_prospects if p.name.lower() == player_name.lower()), None)

            if not prospect:
                print("Player not found.")
                continue

            current_investment = franchise.scouting_investment.get(prospect.name, 0)

            if current_investment >= 3:
                print(f"\n{prospect.name} is already fully scouted (3 points invested).")
                continue

            print(f"\nCurrent scouting investment on {prospect.name}: {current_investment}/3")
            print(f"Available points: {franchise.scouting_points}")
            print("How many points to invest? (1-3, or 0 to cancel)")

            try:
                points = int(input("> ").strip())
                if points == 0:
                    continue

                if points < 1 or points > 3:
                    print("Invalid amount. Must be 1-3 points.")
                    continue

                new_total = current_investment + points
                if new_total > 3:
                    print(f"That would exceed max investment of 3. You can invest {3 - current_investment} more points.")
                    continue

                if points > franchise.scouting_points:
                    print("Not enough scouting points.")
                    continue

                # Invest points
                franchise.scouting_points -= points
                franchise.scouting_investment[prospect.name] = new_total

                print(f"\n✓ Invested {points} point(s) in scouting {prospect.name}")
                print(f"Total investment: {new_total}/3")
                print(f"Remaining points: {franchise.scouting_points}")

            except ValueError:
                print("Invalid input.")

        elif choice == "4":
            # Show top prospects by overall skill
            view_draft_prospects(franchise, min_overall=70)

        elif choice == "5":
            break

        else:
            print("Invalid choice.")


def draft_player(franchise, team, prospect):
    """Add drafted player to team and remove from draft pool"""
    # Remove from draft prospects
    franchise.draft_prospects.remove(prospect)

    # Convert prospect to regular player (remove draft scouting variance)
    prospect.is_draft_prospect = False
    prospect.scouting_variance = {}

    # Add to team
    team.players.append(prospect)

    # Update starters lists based on position
    if prospect.position == "QB":
        team.qb_starters.append(prospect)
    elif prospect.position == "RB":
        team.rb_starters.append(prospect)
    elif prospect.position == "WR":
        team.wr_starters.append(prospect)
    elif prospect.position == "TE":
        team.te_starters.append(prospect)
    elif prospect.position == "OL":
        team.ol_starters.append(prospect)
    elif prospect.position == "DEF":
        team.defense_starters.append(prospect)


def run_draft(franchise):
    """Run the draft with all teams making picks"""
    print(f"\n{'=' * 70}")
    print(f"NFL DRAFT".center(70))
    print(f"{'=' * 70}")

    if not franchise.draft_prospects:
        print("\nNo draft prospects available!")
        return

    # Calculate draft order
    draft_order = calculate_draft_order(franchise.teams)

    print("\n=== DRAFT ORDER ===")
    for idx, team in enumerate(draft_order, 1):
        emoji = get_team_emoji(team.league, team.division)
        print(f"{idx}. {emoji} {team.name} ({team.wins}-{team.losses})")

    input("\nPress Enter to begin the draft...")

    # Run 7 rounds
    num_rounds = 7
    for round_num in range(1, num_rounds + 1):
        print(f"\n{'=' * 70}")
        print(f"ROUND {round_num}".center(70))
        print(f"{'=' * 70}")

        for pick_num, team in enumerate(draft_order, 1):
            overall_pick = (round_num - 1) * len(draft_order) + pick_num

            # Check if user's team is picking
            is_user_team = (team.name == franchise.user_team_name)

            if is_user_team:
                print(f"\n🏈 YOUR PICK! (Round {round_num}, Pick {pick_num}, Overall {overall_pick})")
                print(f"{'=' * 70}")

                while True:
                    print("\n1. View Available Prospects")
                    print("2. Make a Pick")
                    print("3. Auto-pick Best Available")

                    choice = input("> ").strip()

                    if choice == "1":
                        view_draft_prospects(franchise)

                    elif choice == "2":
                        print("\nEnter player name to draft:")
                        player_name = input("> ").strip()

                        prospect = next((p for p in franchise.draft_prospects if p.name.lower() == player_name.lower()), None)

                        if not prospect:
                            print("Player not found or already drafted.")
                            continue

                        # Draft the player
                        draft_player(franchise, team, prospect)
                        print(f"\n✓ {team.name} selects {prospect.name} ({prospect.position}) - Overall: {prospect.skill}")
                        break

                    elif choice == "3":
                        # Auto-pick best available
                        best_prospect = max(franchise.draft_prospects, key=lambda p: p.skill)
                        draft_player(franchise, team, best_prospect)
                        print(f"\n✓ {team.name} selects {best_prospect.name} ({best_prospect.position}) - Overall: {best_prospect.skill}")
                        break

                    else:
                        print("Invalid choice.")

            else:
                # AI teams pick best available player for their needs
                if franchise.draft_prospects:
                    # Simple AI: pick best available
                    best_prospect = max(franchise.draft_prospects, key=lambda p: p.skill)
                    draft_player(franchise, team, best_prospect)

                    emoji = get_team_emoji(team.league, team.division)
                    print(f"{emoji} Pick {overall_pick}: {team.name} selects {best_prospect.name} ({best_prospect.position}) - Overall: {best_prospect.skill}")

        if round_num < num_rounds:
            input(f"\nPress Enter to continue to Round {round_num + 1}...")

    print(f"\n{'=' * 70}")
    print(f"DRAFT COMPLETE!".center(70))
    print(f"{'=' * 70}")
