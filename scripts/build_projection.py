"""Build 2026-27 preseason projection from current rosters (post-offseason).

Approach (mirrors FiveThirtyEight's CARM-Elo idea):
  1. Take each player's 2025-26 BPM and reassign them to their CURRENT team
     after the 2026 offseason (trades + free agency), add top draft rookies.
  2. Each team's roster-projected net rating = Σ BPM · minutes/48 over its top
     rotation (minutes renormalized to a full game).
  3. Blend that with the team's regressed 2025-26 Elo (converted to points) so
     the rating keeps season-tested signal *and* reflects who's on the team now.

Outputs:
  data/players_2027.csv        players on their current teams (+ rookies)
  models/projection_2027.json  per-team 2026-27 power rating (points vs avg)

Run:  python -m scripts.build_projection
"""
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# ---- 2026 offseason: player -> new team (only players who changed teams) ----
MOVES = {
    # Atlanta
    'Devin Carter': 'ATL', 'Luguentz Dort': 'ATL', 'Aaron Wiggins': 'ATL',
    'Ryan Nembhard': 'ATL',
    # Boston
    'Mike Conley': 'BOS', 'Paul George': 'BOS', 'Mitchell Robinson': 'BOS',
    # Brooklyn
    'Keon Ellis': 'BKN', 'Julius Randle': 'BKN', 'Moritz Wagner': 'BKN',
    # Charlotte
    'Grayson Allen': 'CHA', 'Dorian Finney-Smith': 'CHA', 'Royce ONeale': 'CHA',
    'Naz Reid': 'CHA',
    # Chicago
    'Nic Claxton': 'CHI', 'Norman Powell': 'CHI',
    # Dallas
    'Santi Aldama': 'DAL', 'Zaccharie Risacher': 'DAL', 'Marcus Sasser': 'DAL',
    # Denver
    'Marvin Bagley III': 'DEN', 'Lonnie Walker IV': 'DEN',
    # Detroit
    'John Collins': 'DET', 'Gary Harris': 'DET', 'Isaiah Joe': 'DET',
    'Taurean Prince': 'DET',
    # Golden State
    'Al Horford': 'GSW',
    # Houston
    'Bogdan Bogdanovic': 'HOU', 'Marcus Smart': 'HOU',
    # Indiana
    'Larry Nance Jr.': 'IND', 'Kelly Oubre Jr.': 'IND',
    # LA Clippers
    'Gradey Dick': 'LAC', 'Rui Hachimura': 'LAC', 'Brandon Ingram': 'LAC',
    # LA Lakers
    'Quentin Grimes': 'LAL', 'Jaden Hardy': 'LAL', 'Walker Kessler': 'LAL',
    'Kevon Looney': 'LAL', 'Sandro Mamukelashvili': 'LAL', 'Collin Sexton': 'LAL',
    'Matisse Thybulle': 'LAL', 'Ziaire Williams': 'LAL',
    # Memphis
    'Jerami Grant': 'MEM', 'AJ Johnson': 'MEM', 'Kris Murray': 'MEM',
    'Quinten Post': 'MEM', "D'Angelo Russell": 'MEM', 'Isaiah Stewart': 'MEM',
    # Miami
    'Giannis Antetokounmpo': 'MIA', 'Tim Hardaway Jr.': 'MIA', 'Bobby Portis': 'MIA',
    # Milwaukee
    'Tyler Herro': 'MIL', 'Jaime Jaquez Jr.': 'MIL', 'Caris LeVert': 'MIL',
    "Kel'el Ware": 'MIL',
    # Minnesota
    'LaMelo Ball': 'MIN', 'Josh Green': 'MIN', 'Trey Lyles': 'MIN',
    # New York
    'Andre Drummond': 'NYK',
    # Orlando
    'Nikola Vucevic': 'ORL',
    # Philadelphia
    'Jaylen Brown': 'PHI', 'Kentavious Caldwell-Pope': 'PHI', 'LeBron James': 'PHI',
    'Anfernee Simons': 'PHI', 'Dean Wade': 'PHI',
    # Phoenix
    'Miles Bridges': 'PHX', 'Luke Kennard': 'PHX',
    # Portland
    'Ja Morant': 'POR', 'Jeremy Sochan': 'POR',
    # San Antonio
    'Tobias Harris': 'SAS',
    # Toronto
    'Kyle Anderson': 'TOR', 'Kawhi Leonard': 'TOR',
    # Utah
    'Jaxson Hayes': 'UTA', 'Josh Okogie': 'UTA',
    # Washington
    'Deandre Ayton': 'WAS', 'Khris Middleton': 'WAS', 'Trae Young': 'WAS',
}

# ---- top 2026 draft picks (franchise-level talents who will play) ----
# rookies typically land below average; top picks ~ -1 BPM on heavy minutes
ROOKIES = [
    ('AJ Dybantsa', 'WAS', -1.0, 28), ('Darryn Peterson', 'UTA', -1.0, 28),
    ('Cameron Boozer', 'MEM', -0.5, 26), ('Caleb Wilson', 'CHI', -2.0, 20),
    ('Mikel Brown Jr.', 'BKN', -2.0, 22), ('Darius Acuff Jr.', 'SAC', -2.0, 20),
]

REPLACEMENT_BPM = -2.0


def norm(n):
    n = unicodedata.normalize('NFKD', str(n)).encode('ascii', 'ignore').decode()
    return n.lower().replace('.', '').replace("'", '').replace('-', ' ').strip()


def team_net(df):
    """Projected net rating = Σ BPM · minutes/48 over top-10, minutes -> 240."""
    rot = df.sort_values('min_pg', ascending=False).head(10)
    if rot.empty:
        return 0.0
    w = rot.min_pg * (240.0 / rot.min_pg.sum()) / 48.0
    return float((rot.bpm.values * w.values).sum())


def main():
    pl = pd.read_csv(ROOT / 'data' / 'players_2026.csv')
    eng = json.loads((ROOT / 'models' / 'engine.json').read_text())
    elo, b_elo = eng['final_elo'], eng['b_elo_per_point']

    move_norm = {norm(k): v for k, v in MOVES.items()}
    pl['team_2027'] = pl.apply(
        lambda r: move_norm.get(norm(r.athlete_display_name), r.team), axis=1)
    matched = sum(norm(n) in {norm(x.athlete_display_name) for _, x in pl.iterrows()}
                  for n in MOVES)
    print(f'moves defined: {len(MOVES)}, matched to roster: {matched}')

    # add rookies
    rk = pd.DataFrame([{'athlete_id': 90000 + i, 'athlete_display_name': n,
                        'team': t, 'pos': '', 'headshot': '', 'gp': 0,
                        'min_pg': m, 'pts_pg': 0, 'reb_pg': 0, 'ast_pg': 0,
                        'bpm': b, 'impact': round(b * m / 48, 2), 'team_2027': t}
                       for i, (n, t, b, m) in enumerate(ROOKIES)])
    proj = pd.concat([pl, rk], ignore_index=True)
    proj['team'] = proj['team_2027']
    proj = proj.drop(columns=['team_2027'])

    # per-team blend: roster-projected net  +  regressed Elo (as points)
    teams = sorted(proj.team.unique())
    rows = []
    for t in teams:
        roster_net = team_net(proj[proj.team == t])
        elo_net = b_elo * (elo.get(t, 1500) - 1500)          # team pts vs avg
        power = 0.65 * roster_net + 0.35 * (0.75 * elo_net)  # blend + regress
        rows.append({'team': t, 'roster_net': round(roster_net, 2),
                     'elo_net': round(elo_net, 2), 'power': round(power, 2)})
    proj_df = pd.DataFrame(rows).sort_values('power', ascending=False)

    proj[['athlete_id', 'athlete_display_name', 'team', 'pos', 'headshot', 'gp',
          'min_pg', 'pts_pg', 'reb_pg', 'ast_pg', 'bpm', 'impact']].to_csv(
        ROOT / 'data' / 'players_2027.csv', index=False)
    (ROOT / 'models' / 'projection_2027.json').write_text(json.dumps(
        {'power': dict(zip(proj_df.team, proj_df.power)),
         'detail': proj_df.to_dict('records')}, indent=2))

    print('\n2026-27 projected power (points vs league average):')
    for r in proj_df.itertuples():
        print(f'  {r.team:4s} {r.power:+6.2f}   (roster {r.roster_net:+.1f}, '
              f'elo {r.elo_net:+.1f})')


if __name__ == '__main__':
    sys.exit(main())
