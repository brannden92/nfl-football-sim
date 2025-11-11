"""
Standings display utilities for the NFL Football Simulation
"""
from prettytable import PrettyTable


def view_standings(teams, user_team_name=None):
    """Display league standings by division"""
    leagues = {
        "AFC": {"East": [], "North": [], "South": [], "West": []},
        "NFC": {"East": [], "North": [], "South": [], "West": []}
    }

    for team in teams:
        leagues[team.league][team.division].append(team)

    for league_name, divisions in leagues.items():
        print(f"\n{'=' * 60}")
        print(f"{league_name} STANDINGS")
        print(f"{'=' * 60}")

        for div_name, div_teams in divisions.items():
            sorted_teams = sorted(
                div_teams,
                key=lambda t: (t.wins, t.points_for - t.points_against),
                reverse=True
            )
            print(f"\n{league_name} {div_name}")
            print(f"{'-' * 60}")

            table = PrettyTable()
            table.field_names = ["Team", "W", "L", "PF", "PA", "Diff"]

            for team in sorted_teams:
                marker = " *" if team.name == user_team_name else ""
                table.add_row([
                    team.name + marker,
                    team.wins,
                    team.losses,
                    team.points_for,
                    team.points_against,
                    team.points_for - team.points_against
                ])

            print(table)
