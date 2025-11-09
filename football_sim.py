import random
import pickle
from prettytable import PrettyTable

FRANCHISE_LENGTH = 40
SEASON_GAMES = 17

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
        self.retired = False

        # Offensive stats
        self.pass_attempts = 0
        self.pass_completions = 0
        self.pass_yards = 0
        self.pass_td = 0
        self.interceptions = 0
        self.longest_pass = 0

        self.rush_attempts = 0
        self.rush_yards = 0
        self.rush_td = 0
        self.longest_rush = 0

        self.rec_targets = 0
        self.rec_catches = 0
        self.rec_yards = 0
        self.rec_td = 0
        self.drops = 0
        self.longest_rec = 0

        # Defensive stats
        self.tackles = 0
        self.sacks = 0
        self.qb_pressure = 0
        self.interceptions_def = 0
        self.forced_fumbles = 0
        self.fumble_recoveries = 0
        self.pass_deflections = 0

        # Career stats
        self.career_stats = {}
        self.reset_stats()

    def reset_stats(self):
        self.pass_attempts = 0
        self.pass_completions = 0
        self.pass_yards = 0
        self.pass_td = 0
        self.interceptions = 0
        self.longest_pass = 0

        self.rush_attempts = 0
        self.rush_yards = 0
        self.rush_td = 0
        self.longest_rush = 0

        self.rec_targets = 0
        self.rec_catches = 0
        self.rec_yards = 0
        self.rec_td = 0
        self.drops = 0
        self.longest_rec = 0

        self.tackles = 0
        self.sacks = 0
        self.qb_pressure = 0
        self.interceptions_def = 0
        self.forced_fumbles = 0
        self.fumble_recoveries = 0
        self.pass_deflections = 0

    def progress(self):
        if self.retired: return
        if self.age <= 25: change = random.randint(0,3)
        elif self.age <= 29: change = random.randint(-1,2)
        else: change = random.randint(-3,1)
        self.skill = max(50,min(99,self.skill+change))
        self.age += 1
        self.years_played += 1

    def should_retire(self):
        return self.age >= 35

# ============================
# --- TEAM CLASS ---
# ============================
class Team:
    def __init__(self, name):
        self.name = name
        self.players = []
        self.qb_starters = []
        self.rb_starters = []
        self.wr_starters = []
        self.te_starters = []
        self.defense_starters = []
        self.score = 0
        self.wins = 0
        self.losses = 0
        self.points_for = 0
        self.points_against = 0
        self.league = None
        self.division = None

    def reset_score(self):
        self.score = 0
        for p in self.players:
            p.reset_stats()

# ============================
# --- FRANCHISE CLASS ---
# ============================
class Franchise:
    def __init__(self, teams, user_team_name, current_season=1, current_week=1):
        self.teams = teams
        self.user_team_name = user_team_name
        self.current_season = current_season
        self.current_week = current_week

# ============================
# --- CREATE FULL ROSTER ---
# ============================
def create_full_roster(team_name):
    positions = {
        "QB":3, "RB":5, "FB":1, "WR":6, "TE":3,
        "OL":10, "DL":8, "LB":7, "CB":5, "S":4,
        "K":1, "P":1
    }
    players=[]
    for pos,count in positions.items():
        for i in range(count):
            age=random.randint(21,30)
            skill=random.randint(60,85)
            name=f"{team_name} {pos}{i+1}"
            p=Player(name,pos,skill,age)
            players.append(p)
    return players

# ============================
# --- SIMULATE DRIVE ---
# ============================
def simulate_drive(offense,defense):
    qb = offense.qb_starters[0]
    rb = offense.rb_starters[0]
    wr = random.choice(offense.wr_starters + offense.te_starters)
    def_player = random.choice(defense.defense_starters)

    play_type = random.choices(["pass","run"], weights=[0.6,0.4])[0]
    if play_type=="pass":
        qb.pass_attempts += 1
        success = random.random() < 0.55 + (qb.skill-def_player.skill)/200
        if success:
            yards = random.randint(5,40) + wr.skill//10
            qb.pass_completions += 1
            qb.pass_yards += yards
            if yards>qb.longest_pass: qb.longest_pass = yards
            wr.rec_targets += 1
            wr.rec_catches += 1
            wr.rec_yards += yards
            if yards>wr.longest_rec: wr.longest_rec = yards
            if random.random()<0.25:
                qb.pass_td += 1
                wr.rec_td += 1
                offense.score += 7
        else:
            qb.interceptions += 1
            def_player.interceptions_def += 1
    else:
        yards = random.randint(0,15) + rb.skill//10
        rb.rush_attempts += 1
        rb.rush_yards += yards
        if yards>rb.longest_rush: rb.longest_rush = yards
        if random.random()<0.25:
            rb.rush_td += 1
            offense.score += 7

    # Defensive stats
    if random.random()<0.3: def_player.sacks += 1
    if random.random()<0.1: def_player.qb_pressure += 1
    if random.random()<0.05: def_player.forced_fumbles += 1
    if random.random()<0.03: def_player.fumble_recoveries += 1
    if random.random()<0.07: def_player.pass_deflections += 1
    def_player.tackles += random.randint(0,2)

# ============================
# --- SIMULATE GAME ---
# ============================
def simulate_game(team1,team2,user_team=None):
    team1.reset_score()
    team2.reset_score()
    drives_per_team = random.randint(10,14)
    for _ in range(drives_per_team):
        simulate_drive(team1,team2)
        simulate_drive(team2,team1)
    if team1.score>team2.score: winner=team1
    elif team2.score>team1.score: winner=team2
    else: 
        winner=random.choice([team1,team2])
        winner.score += 3
    team1.points_for += team1.score
    team1.points_against += team2.score
    team2.points_for += team2.score
    team2.points_against += team1.score
    if winner==team1:
        team1.wins+=1
        team2.losses+=1
    else:
        team2.wins+=1
        team1.losses+=1
    if user_team is None or user_team in [team1.name, team2.name]:
        print(f"{team1.name} {team1.score} - {team2.name} {team2.score}")
    return winner

# ============================
# --- VIEW TEAM STATS ---
# ============================
def print_team_stats(team):
    print("\n=== Passing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Comp","Att","Yards","TD","INT","Comp%","Y/A","Long"]
    qbs = sorted(team.qb_starters,key=lambda x:x.pass_yards,reverse=True)
    for qb in qbs:
        comp_pct = qb.pass_completions/qb.pass_attempts*100 if qb.pass_attempts else 0
        ypa = qb.pass_yards/qb.pass_attempts if qb.pass_attempts else 0
        table.add_row([qb.name,qb.pass_completions,qb.pass_attempts,qb.pass_yards,
                       qb.pass_td,qb.interceptions,round(comp_pct,1),round(ypa,1),qb.longest_pass])
    print(table)

    print("\n=== Rushing Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Att","Yards","TD","Y/A","Long"]
    rbs = sorted(team.rb_starters,key=lambda x:x.rush_yards,reverse=True)[:2]
    for rb in rbs:
        ya = rb.rush_yards/rb.rush_attempts if rb.rush_attempts else 0
        table.add_row([rb.name,rb.rush_attempts,rb.rush_yards,rb.rush_td,round(ya,1),rb.longest_rush])
    print(table)

    print("\n=== Receiving Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Rec","Targets","Yards","TD","Y/R","Drops","Long"]
    receivers = sorted(team.wr_starters + team.te_starters,key=lambda x:x.rec_yards,reverse=True)[:4]
    for r in receivers:
        ypr = r.rec_yards/r.rec_catches if r.rec_catches else 0
        table.add_row([r.name,r.rec_catches,r.rec_targets,r.rec_yards,r.rec_td,round(ypr,1),r.drops,r.longest_rec])
    print(table)

    print("\n=== Defensive Leaders ===")
    table = PrettyTable()
    table.field_names = ["Name","Tackles","Sacks","QB Pressure","INT","FF","FR","PD"]
    defenders = sorted(team.defense_starters,key=lambda x:(x.tackles+x.sacks),reverse=True)[:5]
    for d in defenders:
        table.add_row([d.name,d.tackles,d.sacks,d.qb_pressure,d.interceptions_def,d.forced_fumbles,d.fumble_recoveries,d.pass_deflections])
    print(table)

# ============================
# --- SAVE / LOAD ---
# ============================
def save_franchise(franchise, filename="franchise_save.pkl"):
    with open(filename,"wb") as f:
        pickle.dump(franchise,f)
    print(f"Saved franchise to {filename}")

def load_franchise(filename="franchise_save.pkl"):
    try:
        with open(filename,"rb") as f:
            franchise = pickle.load(f)
        print(f"Loaded franchise from {filename}")
        return franchise
    except:
        return None

# ============================
# --- CREATE NEW LEAGUE ---
# ============================
def create_new_league():
    team_names=[
        "Sharks","Wolves","Eagles","Tigers","Lions","Bears","Panthers","Vikings",
        "Ravens","Jets","Patriots","Dolphins","Texans","Colts","Steelers","Bengals",
        "Packers","Falcons","Saints","Buccaneers","Chargers","Raiders","Chiefs","Broncos",
        "Cardinals","Seahawks","49ers","Rams","Giants","Cowboys","Jaguars","Titans"
    ]
    leagues={"AFC":{"East":[],"North":[],"South":[],"West":[]},"NFC":{"East":[],"North":[],"South":[],"West":[]}}
    idx=0
    for league_name,divs in leagues.items():
        for div_name in divs:
            for _ in range(4):
                team = Team(team_names[idx])
                team.players = create_full_roster(team.name)
                team.qb_starters = [p for p in team.players if p.position=="QB"][:1]
                team.rb_starters = [p for p in team.players if p.position=="RB"][:2]
                team.wr_starters = [p for p in team.players if p.position=="WR"][:2]
                team.te_starters = [p for p in team.players if p.position=="TE"][:2]
                team.defense_starters = [p for p in team.players if p.position in ["DL","LB","CB","S"]]
                team.league = league_name
                team.division = div_name
                leagues[league_name][div_name].append(team)
                idx += 1
    teams = [t for l in leagues.values() for d in l.values() for t in d]
    return teams

# ============================
# --- RUN FRANCHISE MENU ---
# ============================
def run_franchise(franchise):
    retired_players=[]
    while franchise.current_season <= FRANCHISE_LENGTH:
        print(f"\n===== SEASON {franchise.current_season} =====")
        for t in franchise.teams:
            t.reset_score()
        weekly_schedule = list(range(1,SEASON_GAMES+1))
        while franchise.current_week <= SEASON_GAMES:
            print(f"\n--- WEEK {franchise.current_week} ---")
            user_team = next(t for t in franchise.teams if t.name==franchise.user_team_name)
            print("1. Simulate Week")
            print("2. View Your Team Stats")
            print("3. View Other Teams Stats")
            print("4. View Standings")
            print("5. Save Franchise")
            choice=input("> ").strip()
            if choice=="1":
                # Random matchups
                for i in range(0,len(franchise.teams),2):
                    simulate_game(franchise.teams[i],franchise.teams[i+1],user_team=franchise.user_team_name)
                franchise.current_week += 1
            elif choice=="2":
                print_team_stats(user_team)
            elif choice=="3":
                for idx,t in enumerate(franchise.teams):
                    print(f"{idx+1}. {t.name}")
                sel=int(input("Select team: "))-1
                print_team_stats(franchise.teams[sel])
            elif choice=="4":
                view_standings(franchise.teams,user_team_name=franchise.user_team_name)
            elif choice=="5":
                save_franchise(franchise)
            else:
                print("Invalid choice.")
        franchise.current_season += 1
        franchise.current_week = 1

# ============================
# --- MAIN LOOP ---
# ============================
def main():
    print("=== NFL Franchise Simulator ===")
    print("1. New Game\n2. Load Game")
    choice=input("> ").strip()
    if choice=="2":
        franchise=load_franchise()
        if franchise is None:
            teams=create_new_league()
            for i,t in enumerate(teams): print(f"{i+1}. {t.name}")
            sel=int(input("Select your team: "))-1
            franchise=Franchise(teams,teams[sel].name)
    else:
        teams=create_new_league()
        for i,t in enumerate(teams): print(f"{i+1}. {t.name}")
        sel=int(input("Select your team: "))-1
        franchise=Franchise(teams,teams[sel].name)
    run_franchise(franchise)
    save_franchise(franchise)
    print("Franchise complete!")

if __name__=="__main__":
    main()
