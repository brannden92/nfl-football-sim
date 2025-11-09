import random
import pickle
from prettytable import PrettyTable

# ============================
# --- PLAYER CLASS ---
# ============================
class Player:
    def __init__(self, name, position, skill, age):
        self.name = name
        self.position = position
        self.skill = skill
        self.age = age
        self.years_played = 0
        self.stats = {k: 0 for k in ["pass_yards", "pass_td", "int", "rush_yards", "rush_td", "rec_yards", "rec_td", "sacks"]}
        self.playoff_stats = self.stats.copy()
        self.career_stats = self.stats.copy()
        self.retired = False

    def reset_season_stats(self):
        self.stats = {k: 0 for k in self.stats}
        self.playoff_stats = {k: 0 for k in self.playoff_stats}

    def progress(self):
        if self.retired:
            return
        if self.age <= 25:
            change = random.randint(0, 3)
        elif self.age <= 29:
            change = random.randint(-1, 2)
        else:
            change = random.randint(-3, 1)
        self.skill = max(50, min(99, self.skill + change))
        self.age += 1
        self.years_played += 1

    def should_retire(self):
        return self.age >= 35


# ============================
# --- TEAM CLASS ---
# ============================
class Team:
    def __init__(self, name, qb, rb, wr, defense):
        self.name = name
        self.qb = qb
        self.rb = rb
        self.wr = wr
        self.defense = defense
        self.players = [qb, rb, wr, defense]
        self.score = 0
        self.wins = 0
        self.losses = 0
        self.points_for = 0
        self.points_against = 0

    def reset_score(self):
        self.score = 0


# ============================
# --- SIMULATION FUNCTIONS ---
# ============================
def simulate_drive(offense, defense, playoff=False):
    qb, rb, wr = offense.qb, offense.rb, offense.wr
    def_player = defense.defense  # ✅ FIX: get defense player

    stats = qb.playoff_stats if playoff else qb.stats
    rb_stats = rb.playoff_stats if playoff else rb.stats
    wr_stats = wr.playoff_stats if playoff else wr.stats
    def_stats = def_player.playoff_stats if playoff else def_player.stats  # ✅ FIX

    play_type = random.choice(["pass", "run"])

    if play_type == "pass":
        success = random.random() < 0.55 + (qb.skill - def_player.skill) / 200
        if success:
            yards = random.randint(10, 40) + wr.skill // 10
            stats["pass_yards"] += yards
            wr_stats["rec_yards"] += yards
            if yards > 20 and random.random() < 0.3:
                stats["pass_td"] += 1
                wr_stats["rec_td"] += 1
                offense.score += 7
        else:
            stats["int"] += 1
            def_stats["int"] += 1
    else:
        yards = random.randint(0, 15) + rb.skill // 10
        rb_stats["rush_yards"] += yards
        if yards > 10 and random.random() < 0.25:
            rb_stats["rush_td"] += 1
            offense.score += 7


def simulate_game(team1, team2, playoff=False):
    team1.reset_score()
    team2.reset_score()

    for _ in range(4):
        simulate_drive(team1, team2, playoff)
        simulate_drive(team2, team1, playoff)

    if random.random() < 0.3:
        (team1.defense.playoff_stats if playoff else team1.defense.stats)["sacks"] += 1
    if random.random() < 0.3:
        (team2.defense.playoff_stats if playoff else team2.defense.stats)["sacks"] += 1

    if team1.score > team2.score:
        return team1, f"{team1.name} {team1.score} - {team2.name} {team2.score}"
    elif team2.score > team1.score:
        return team2, f"{team1.name} {team1.score} - {team2.name} {team2.score}"
    else:
        winner = random.choice([team1, team2])
        winner.score += 3
        return winner, f"{team1.name} {team1.score} - {team2.name} {team2.score} (OT)"


def simulate_season(teams):
    results = []
    for t in teams:
        t.wins = t.losses = t.points_for = t.points_against = 0

    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            winner, result = simulate_game(teams[i], teams[j])
            results.append(result)
            teams[i].points_for += teams[i].score
            teams[i].points_against += teams[j].score
            teams[j].points_for += teams[j].score
            teams[j].points_against += teams[i].score
            if winner == teams[i]:
                teams[i].wins += 1
                teams[j].losses += 1
            else:
                teams[j].wins += 1
                teams[i].losses += 1

    table = PrettyTable()
    table.field_names = ["Team", "W", "L", "PF", "PA", "Diff"]
    sorted_teams = sorted(teams, key=lambda t: (t.wins, t.points_for - t.points_against), reverse=True)
    for team in sorted_teams:
        table.add_row([team.name, team.wins, team.losses, team.points_for, team.points_against, team.points_for - team.points_against])

    return results, table, sorted_teams


def simulate_playoffs(sorted_teams):
    print("\n--- Playoffs ---")
    for team in sorted_teams:
        for player in team.players:
            player.playoff_stats = {k: 0 for k in player.playoff_stats}

    playoff_results = []
    semi1_winner, res1 = simulate_game(sorted_teams[0], sorted_teams[3], playoff=True)
    semi2_winner, res2 = simulate_game(sorted_teams[1], sorted_teams[2], playoff=True)
    playoff_results.append("Semifinal 1: " + res1)
    playoff_results.append("Semifinal 2: " + res2)

    champ, final = simulate_game(semi1_winner, semi2_winner, playoff=True)
    playoff_results.append("Championship: " + final)

    print("\n".join(playoff_results))
    print(f"\n🏆 Champion: {champ.name}")
    return champ


# ============================
# --- MVP & STATS ---
# ============================
def calculate_mvp(teams, playoff=False):
    best_player = None
    best_score = -999
    for team in teams:
        for p in team.players:
            stats = p.playoff_stats if playoff else p.stats
            score = (stats["pass_yards"] / 25 + stats["pass_td"] * 4 - stats["int"] * 2 +
                     stats["rush_yards"] / 10 + stats["rush_td"] * 6 +
                     stats["rec_yards"] / 10 + stats["rec_td"] * 6 +
                     stats["sacks"] * 2)
            if score > best_score:
                best_score = score
                best_player = (p, team.name, stats)
    if best_player:
        p, team_name, stats = best_player
        label = "Playoff MVP" if playoff else "Season MVP"
        print(f"\n🏅 {label}: {p.name} ({team_name}, {p.position})")
        print(f"   PassYds: {stats['pass_yards']} | PassTD: {stats['pass_td']} | INT: {stats['int']}")
        print(f"   RushYds: {stats['rush_yards']} | RushTD: {stats['rush_td']}")
        print(f"   RecYds: {stats['rec_yards']} | RecTD: {stats['rec_td']}")
        print(f"   Sacks: {stats['sacks']}")


# ============================
# --- RETIREMENTS & DRAFT ---
# ============================
def draft_replacements(team, retired_players):
    for p in retired_players:
        skill = random.randint(65, 80)
        age = random.randint(21, 23)
        name = random.choice(["Walker", "King", "Carter", "Harris", "Adams", "Ward", "Scott", "Brooks"])
        rookie = Player(name, p.position, skill, age)
        print(f"🆕 {team.name} drafted {rookie.name} ({rookie.position}, {rookie.skill} OVR, age {rookie.age}) to replace {p.name}")
        for i, pl in enumerate(team.players):
            if pl == p:
                team.players[i] = rookie
                if p.position == "QB": team.qb = rookie
                elif p.position == "RB": team.rb = rookie
                elif p.position == "WR": team.wr = rookie
                elif p.position == "DEF": team.defense = rookie
                break


def handle_retirements_and_drafts(teams, retired_list):
    for team in teams:
        retired_players = []
        for p in team.players:
            if not p.retired and p.should_retire():
                p.retired = True
                retired_players.append(p)
                retired_list.append(p)
                print(f"🏁 {p.name} ({p.position}, {team.name}) retired at age {p.age}")
        if retired_players:
            draft_replacements(team, retired_players)


def print_career_summary(all_players):
    print("\n===== CAREER SUMMARY =====")
    table = PrettyTable()
    table.field_names = ["Player", "Pos", "Age", "Skill", "Years", "PassYds", "PassTD", "RushYds", "RushTD", "RecYds", "RecTD", "Sacks"]
    for p in sorted(all_players, key=lambda x: x.years_played, reverse=True):
        table.add_row([p.name, p.position, p.age, p.skill, p.years_played,
                       p.career_stats["pass_yards"], p.career_stats["pass_td"],
                       p.career_stats["rush_yards"], p.career_stats["rush_td"],
                       p.career_stats["rec_yards"], p.career_stats["rec_td"],
                       p.career_stats["sacks"]])
    print(table)


# ============================
# --- SAVE / LOAD ---
# ============================
def save_franchise(teams, filename="franchise_save.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(teams, f)
    print(f"\n💾 Franchise saved to {filename}")


def load_franchise(filename="franchise_save.pkl"):
    with open(filename, "rb") as f:
        teams = pickle.load(f)
    print(f"\n📂 Franchise loaded from {filename}")
    return teams


# ============================
# --- MAIN LOOP ---
# ============================
def run_multiple_seasons(teams, seasons=5, save_every=1):
    all_players = [p for t in teams for p in t.players]
    retired_players = []

    for year in range(1, seasons + 1):
        print(f"\n\n===== SEASON {year} =====\n")
        for team in teams:
            for p in team.players:
                p.reset_season_stats()

        results, standings, sorted_teams = simulate_season(teams)
        print("\n--- Season Standings ---")
        print(standings)
        calculate_mvp(teams, playoff=False)

        champ = simulate_playoffs(sorted_teams)
        calculate_mvp(sorted_teams, playoff=True)

        for team in teams:
            for p in team.players:
                for k in p.stats:
                    p.career_stats[k] += p.stats[k]

        for team in teams:
            for p in team.players:
                p.progress()

        handle_retirements_and_drafts(teams, retired_players)
        all_players = [p for p in all_players if not p.retired] + retired_players
        retired_players.clear()

        if year % save_every == 0:
            save_franchise(teams)

    print_career_summary(all_players)


# ============================
# --- ENTRY POINT ---
# ============================
def main():
    choice = input("Load saved franchise? (y/n): ").strip().lower()
    if choice == "y":
        teams = load_franchise()
    else:
        teams = [
            Team("Sharks", Player("Smith", "QB", 80, 24), Player("Brown", "RB", 75, 23), Player("Davis", "WR", 78, 22), Player("Lee", "DEF", 82, 26)),
            Team("Wolves", Player("Johnson", "QB", 76, 25), Player("Miller", "RB", 70, 27), Player("Garcia", "WR", 74, 24), Player("White", "DEF", 80, 28)),
            Team("Eagles", Player("Wilson", "QB", 72, 22), Player("Moore", "RB", 68, 23), Player("Taylor", "WR", 71, 22), Player("Clark", "DEF", 77, 27)),
            Team("Tigers", Player("Anderson", "QB", 74, 24), Player("Hall", "RB", 73, 26), Player("Allen", "WR", 76, 25), Player("Young", "DEF", 79, 28)),
        ]

    seasons = int(input("How many seasons do you want to simulate? "))
    run_multiple_seasons(teams, seasons=seasons, save_every=1)
    print("\nGame complete — all seasons finished!")


if __name__ == "__main__":
    main()
