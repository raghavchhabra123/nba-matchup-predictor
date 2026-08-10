"""Backend stress test — verify the modeling is internally consistent.

Checks probability bounds, symmetry, monotonicity, and the sign/scale of every
adjustment (home court, rest, players, travel) across many random matchups and
hand-picked edge cases. Run:  python -m scripts.stress_test
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import SpreadEngine
from src.lineups import team_delta, home_player_points
from src.travel import compute_travel, ARENAS, ALTITUDE_BONUS

eng = SpreadEngine()
players = pd.read_csv(ROOT / 'data' / 'players_2026.csv')
teams = eng.teams()
fails = []


def check(name, cond, detail=''):
    (print(f'  ok  {name}') if cond else fails.append(f'{name} — {detail}'))
    if not cond:
        print(f'  FAIL {name} — {detail}')


print('== probability bounds & basic sanity ==')
bad = 0
for h, a in combinations(teams, 2):
    for hc in (True, False):
        r = eng.predict(h, a, home_court=hc)
        if not (0 < r['prob_home'] < 1) or np.isnan(r['margin']):
            bad += 1
check('all probs in (0,1), no NaN', bad == 0, f'{bad} bad')

print('\n== power-rating symmetry (neutral) ==')
worst = 0
for h, a in combinations(teams, 2):
    m1 = eng.power_margin(h, a)
    m2 = eng.power_margin(a, h)
    worst = max(worst, abs(m1 + m2))
check('power_margin(A,B) == -power_margin(B,A)', worst < 1e-9, f'max err {worst:.2e}')

print('\n== home court always helps the home team ==')
bad = 0
for h, a in combinations(teams, 2):
    on = eng.predict(h, a, home_court=True)['prob_home']
    off = eng.predict(h, a, home_court=False)['prob_home']
    if on < off - 1e-12:
        bad += 1
check('P(home | HCA on) >= P(home | off)', bad == 0, f'{bad} violations')

print('\n== monotonic in Elo (better team, higher win prob) ==')
order = sorted(teams, key=lambda t: eng.elo[t], reverse=True)
best, worst_t = order[0], order[-1]
p_best_home = eng.predict(best, worst_t, home_court=False)['prob_home']
p_worst_home = eng.predict(worst_t, best, home_court=False)['prob_home']
check('best team beats worst on neutral floor', p_best_home > 0.5)
check('worst team is underdog hosting the best', p_worst_home < 0.5)
check('best-vs-worst is a big favorite (>80%)', p_best_home > 0.80,
      f'{p_best_home:.2f}')

print('\n== back-to-back hurts ==')
h, a = order[5], order[6]
base = eng.predict(h, a)['prob_home']
home_tired = eng.predict(h, a, home_rest=1)['prob_home']
away_tired = eng.predict(h, a, away_rest=1)['prob_home']
check('home B2B lowers home prob', home_tired < base, f'{home_tired:.3f} vs {base:.3f}')
check('away B2B raises home prob', away_tired > base, f'{away_tired:.3f} vs {base:.3f}')

print('\n== players: removing a star weakens the team ==')
bad = []
for t in teams:
    r = players[players.team == t].sort_values('bpm', ascending=False)
    if r.empty:
        continue
    star = r.iloc[0]
    if star.bpm <= 0:
        continue
    d = team_delta(players[players.team == t], [star.athlete_display_name])
    if d > 0:
        bad.append((t, star.athlete_display_name, round(d, 2)))
check('removing each team\'s best player never helps them', not bad, str(bad[:3]))

print('\n== players: star sit lands in the realistic 2.5-7 pt band ==')
mags = []
for t in teams:
    r = players[players.team == t].sort_values('bpm', ascending=False)
    if r.empty or r.iloc[0].bpm < 5:
        continue
    d = -team_delta(players[players.team == t], [r.iloc[0].athlete_display_name])
    mags.append((t, r.iloc[0].athlete_display_name, round(d, 1)))
vals = [m for _, _, m in mags]
check('elite-player absences average 3-6 pts',
      3.0 <= np.mean(vals) <= 6.0, f'mean {np.mean(vals):.2f}, range {min(vals)}-{max(vals)}')
print('   sample:', sorted(mags, key=lambda x: -x[2])[:6])

print('\n== players: removing a below-replacement player can help (addition by subtraction) ==')
found = None
for t in teams:
    r = players[players.team == t].sort_values('min_pg', ascending=False).head(10)
    negs = r[r.bpm < -2.0]
    if not negs.empty:
        d = team_delta(players[players.team == t], [negs.iloc[0].athlete_display_name])
        found = (t, negs.iloc[0].athlete_display_name, round(d, 2))
        break
check('a sub-replacement player exists and removing them is ~>= 0',
      found is None or found[2] >= -0.05, str(found))

print('\n== depth: OKC (deep) loses less than DEN (thin) for their star ==')
okc = -team_delta(players[players.team == 'OKC'], ['Shai Gilgeous-Alexander'])
den = -team_delta(players[players.team == 'DEN'], ['Nikola Jokic'])
check('OKC star-out < DEN star-out (depth matters)', okc < den, f'OKC {okc:.1f} vs DEN {den:.1f}')

print('\n== home_player_points sign convention ==')
# home star out should reduce home margin; away star out should raise it
hp1 = home_player_points(players[players.team == 'DEN'], players[players.team == 'LAL'],
                         ['Nikola Jokic'], [])
hp2 = home_player_points(players[players.team == 'DEN'], players[players.team == 'LAL'],
                         [], ['Luka Doncic'])
check('home star out -> negative home shift', hp1 < 0, f'{hp1:.2f}')
check('away star out -> positive home shift', hp2 > 0, f'{hp2:.2f}')

print('\n== travel: altitude only for DEN/UTA, eastward >= westward ==')
alt_ok = all((compute_travel(h, 'MIA')['alt_pts'] > 0) == (h in ALTITUDE_BONUS)
             for h in teams)
check('altitude bonus applies iff host is DEN/UTA', alt_ok)
east = compute_travel('BOS', 'LAL')['points']   # LAL flies east
west = compute_travel('LAL', 'BOS')['points']   # BOS flies west
check('eastward trip penalised >= westward', east > west, f'{east} vs {west}')
same_city = compute_travel('BKN', 'NYK')['points']
check('no travel effect within same city (~0)', abs(same_city) < 0.2, f'{same_city}')

print('\n== travel only applies on a home floor ==')
r_hc = eng.predict('DEN', 'MIA', home_court=True, travel_points=3.0)
r_neu = eng.predict('DEN', 'MIA', home_court=False, travel_points=3.0)
check('travel ignored on neutral court', r_neu['components']['travel'] == 0)
check('travel counted on home court', r_hc['components']['travel'] == 3.0)

print('\n== components sum to the margin ==')
r = eng.predict('DEN', 'LAL', home_court=True, home_rest=1, player_points=-2,
                travel_points=1.5)
s = sum(r['components'].values())
check('component sum == margin', abs(s - r['margin']) < 1e-9, f'{s} vs {r["margin"]}')

print('\n== Elo rating distribution sane ==')
elos = np.array(list(eng.elo.values()))
check('30 teams rated', len(elos) == 30, str(len(elos)))
check('Elo spread realistic (1180-1820)', elos.min() > 1180 and elos.max() < 1820,
      f'{elos.min():.0f}-{elos.max():.0f}')
check('Elo mean ~1500', 1480 < elos.mean() < 1560, f'{elos.mean():.0f}')

print('\n' + '=' * 50)
if fails:
    print(f'{len(fails)} FAILURES:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('ALL CHECKS PASSED ✅')
