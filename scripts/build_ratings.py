"""Build the point-spread engine: Elo ratings + fitted margin model.

Fits   margin ~ a0 + b_elo*elo_diff + c_h*home_b2b + c_a*away_b2b
where a0 (intercept) is the home-court advantage in POINTS, and the residual
SD is the sigma used to convert margins to win probabilities via the normal CDF.

Saves:
  models/engine.json          # coefficients, sigma, HCA, B2B penalties, ratings
  data/elo_ratings_2026.csv   # final neutral Elo + season net rating per team

Run:  python -m scripts.build_ratings
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.elo import HCA_ELO, compute_elo  # noqa: E402
from src.ratings import add_net_rating, add_rest_flags  # noqa: E402

TRAIN_MAX = 2023  # fit on <=2023-24; hold out 2024-25 & 2025-26


def fit_ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return beta  # [intercept, *coefs]


def main():
    games = pd.read_csv(ROOT / 'data' / 'games_history.csv', parse_dates=['date'])
    g, final = compute_elo(games)
    g = add_rest_flags(g)
    g = add_net_rating(g)
    g['margin'] = g.home_pts - g.away_pts

    d = g.dropna(subset=['elo_diff_pre', 'home_b2b', 'away_b2b', 'margin']).copy()
    train = d[d.season <= TRAIN_MAX]

    Xcols = ['elo_diff_pre', 'home_b2b', 'away_b2b']
    beta = fit_ols(train[Xcols].values, train['margin'].values)
    a0, b_elo, c_h, c_a = beta

    # Home court has declined over time — refit the intercept on the modern era
    # (2016+) so it reflects today's ~2-pt reality instead of the 2003-2026 blend.
    recent = train[train.season >= 2016]
    beta_r = fit_ols(recent[Xcols].values, recent['margin'].values)
    a0 = beta_r[0]          # use recent-era home-court advantage
    c_h, c_a = beta_r[2], beta_r[3]
    print(f'HCA all-history {beta[0]:+.2f} -> recent-era {a0:+.2f} pts')
    pred_train = (np.column_stack([np.ones(len(train)), train[Xcols].values]) @ beta)
    sigma = float(np.sqrt(np.mean((train['margin'].values - pred_train) ** 2)))

    # Season net rating per team from the most recent season (for display + context)
    last_season = int(g.season.max())
    gs = g[g.season == last_season]
    nr = {}
    for team in final:
        home_m = (gs[gs.home == team].home_pts - gs[gs.home == team].away_pts)
        away_m = (gs[gs.away == team].away_pts - gs[gs.away == team].home_pts)
        margins = pd.concat([home_m, away_m])
        if len(margins):
            nr[team] = round(float(margins.mean()), 2)

    engine = {
        'intercept_hca_points': round(float(a0), 3),
        'b_elo_per_point': round(float(b_elo), 5),
        'home_b2b_points': round(float(c_h), 3),
        'away_b2b_points': round(float(c_a), 3),
        'sigma_points': round(sigma, 3),
        'hca_elo': HCA_ELO,
        'points_per_100_elo': round(float(b_elo) * 100, 3),
        'train_seasons': f'2003-{TRAIN_MAX}',
        'final_elo': {k: round(v, 1) for k, v in final.items()},
        'season_net_rating': nr,
        'last_season': last_season,
    }
    (ROOT / 'models').mkdir(exist_ok=True)
    (ROOT / 'models' / 'engine.json').write_text(json.dumps(engine, indent=2))

    rows = [{'team': t, 'elo': round(final[t], 1),
             'net_rating': nr.get(t, np.nan)} for t in final]
    pd.DataFrame(rows).to_csv(ROOT / 'data' / 'elo_ratings_2026.csv', index=False)

    print(f'Home-court advantage: {a0:+.2f} pts   (Elo HCA {HCA_ELO:.0f})')
    print(f'Elo -> points:        {b_elo*100:.2f} pts per 100 Elo')
    print(f'Home B2B penalty:     {c_h:+.2f} pts   Away B2B: {c_a:+.2f} pts')
    print(f'Residual sigma:       {sigma:.2f} pts')
    print('\nTop 6 neutral Elo:')
    for t in list(final)[:6]:
        print(f'  {t:4s} {final[t]:6.0f}   net {nr.get(t, float("nan")):+.1f}')
    print('\nsaved models/engine.json, data/elo_ratings_2026.csv')


if __name__ == '__main__':
    main()
