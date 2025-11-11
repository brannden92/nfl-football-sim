"""
Main entry point for the NFL Football Simulation
"""
import random
from config import FRANCHISE_LENGTH, SEASON_GAMES
from models import Franchise
from game import simulate_game, run_playoffs
from utils import (
    create_new_league, save_franchise, load_franchise,
    print_team_summary, print_team_stats, print_last_game_stats,
    view_standings
)


def run_franchise(franchise):
    """Run the franchise mode with season loop"""
    retired_players = []

    while franchise.current_season <= FRANCHISE_LENGTH:
        print(f"\n{'=' * 70}")
        print(f"SEASON {franchise.current_season}".center(70))
        print(f"{'=' * 70}")

        # Reset season records
        for t in franchise.teams:
            t.wins = 0
            t.losses = 0
            t.points_for = 0
            t.points_against = 0
            t.score = 0
            # Reset all player stats at start of season
            for p in t.players:
                p.reset_stats()

        # Regular season
        while franchise.current_week <= SEASON_GAMES:
            print(f"\n{'=' * 70}")
            print(f"WEEK {franchise.current_week}".center(70))
            print(f"{'=' * 70}")

            user_team = next(t for t in franchise.teams if t.name == franchise.user_team_name)

            print("1. Simulate Week")
            print("2. View Last Game's Stats")
            print("3. View Your Team Season Stats")
            print("4. View Other Team Stats")
            print("5. View Standings")
            print("6. Save Franchise")
            print("7. Quit")
            choice = input("> ").strip()

            if choice == "1":
                # Simulate all games for the week (shuffle / pairing)
                random.shuffle(franchise.teams)
                for i in range(0, len(franchise.teams), 2):
                    simulate_game(franchise.teams[i], franchise.teams[i + 1], user_team=franchise.user_team_name)

                # Show user team summary after each week
                print_team_summary(user_team, franchise.teams)
                franchise.current_week += 1

            elif choice == "2":
                # Last game's stats (per-player deltas)
                print_last_game_stats(user_team)

            elif choice == "3":
                # Season totals (accumulated)
                games_played = franchise.current_week - 1
                print_team_stats(user_team, games_played)

            elif choice == "4":
                games_played = franchise.current_week - 1
                for idx, t in enumerate(franchise.teams):
                    print(f"{idx + 1}. {t.name}")
                try:
                    sel = int(input("Select team: ")) - 1
                    if 0 <= sel < len(franchise.teams):
                        print_team_stats(franchise.teams[sel], games_played)
                except:
                    print("Invalid selection.")

            elif choice == "5":
                view_standings(franchise.teams, user_team_name=franchise.user_team_name)

            elif choice == "6":
                save_franchise(franchise)

            elif choice == "7":
                save_franchise(franchise)
                return

            else:
                print("Invalid choice.")

        # Season complete - run playoffs
        print(f"\n{'=' * 70}")
        print("REGULAR SEASON COMPLETE".center(70))
        print(f"{'=' * 70}")
        view_standings(franchise.teams, user_team_name=franchise.user_team_name)

        input("\nPress Enter to start the playoffs...")
        champion = run_playoffs(franchise)

        # Progress players (aging, skill changes, retirements)
        print("\n=== OFF-SEASON ===")
        for team in franchise.teams:
            for player in team.players:
                player.progress()
                if player.should_retire() and not player.retired:
                    player.retired = True
                    retired_players.append(player)
                    print(f"{player.name} ({team.name}) has retired at age {player.age}")

        franchise.current_season += 1
        franchise.current_week = 1

        input("\nPress Enter to continue to next season...")

    print("\n" + "=" * 70)
    print("FRANCHISE COMPLETE!".center(70))
    print("=" * 70)


def main():
    """Main entry point"""
    print("=== NFL Franchise Simulator ===")
    print("1. New Game\n2. Load Game")
    choice = input("> ").strip()

    if choice == "2":
        franchise = load_franchise()
        if franchise is None:
            print("No save file found. Starting new game...")
            teams = create_new_league()
            for i, t in enumerate(teams):
                print(f"{i + 1}. {t.name}")
            sel = int(input("Select your team: ")) - 1
            franchise = Franchise(teams, teams[sel].name)
    else:
        teams = create_new_league()
        for i, t in enumerate(teams):
            print(f"{i + 1}. {t.name}")
        sel = int(input("Select your team: ")) - 1
        franchise = Franchise(teams, teams[sel].name)

    run_franchise(franchise)

    save_franchise(franchise)
    print("Franchise complete!")


if __name__ == "__main__":
    main()
