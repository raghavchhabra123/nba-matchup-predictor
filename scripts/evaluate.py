"""Holdout evaluation + calibration for the point-spread engine vs baselines.

Holdout = 2024-25 and 2025-26 (strictly out-of-sample future seasons).
Compares:
  - Spread engine (Elo margin + HCA + rest -> normal CDF)   [Tier 1]
  - Elo-only baseline (logistic on Elo diff + Elo HCA)
  - Win-rate classifier (original notebook features)
  - Naive "home team wins" at the league home rate

Metrics: accuracy, log-loss, Brier, plus a 10-bin reliability table.
Saves models/metrics_tier1.json.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.elo import compute_elo, win_prob_from_elo  # noqa: E402
from src.engine import SpreadEngine, _phi  # noqa: E402
from src.features import MODEL_COLS, build_training_frame  # noqa: E402
from src.ratings import add_rest_flags  # noqa: E402

HOLDOUT = [2024, 2025]


def scores(y, p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    y = np.asarray(y)
    return {
        'accuracy': round(float(((p > 0.5) == (y == 1)).mean()), 4),
        'log_loss': round(float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()), 4),
        'brier': round(float(((p - y) ** 2).mean()), 4),
        'n': int(len(y)),
    }


def reliability(y, p, bins=10):
    y, p = np.asarray(y), np.asarray(p)
    edges = np.linspace(0, 1, bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if m.sum() >= 15:
            out.append({'bin': round((lo + hi) / 2, 2),
                        'predicted': round(float(p[m].mean()), 3),
                        'observed': round(float(y[m].mean()), 3),
                        'n': int(m.sum())})
    return out


def main():
    games = pd.read_csv(ROOT / 'data' / 'games_history.csv', parse_dates=['date'])
    g, _ = compute_elo(games)
    g = add_rest_flags(g)
    eng = SpreadEngine()

    test = g[g.season.isin(HOLDOUT)].dropna(subset=['elo_diff_pre']).copy()
    y = test.home_win.values

    # --- Spread engine (Tier 1) ---
    margin = (eng.b_elo * test.elo_diff_pre + eng.hca
              + eng.home_b2b * test.home_b2b + eng.away_b2b * test.away_b2b)
    p_spread = np.array([_phi(m / eng.sigma) for m in margin.values])

    # --- Elo-only baseline ---
    p_elo = np.array([win_prob_from_elo(d, eng.p['hca_elo'], True)
                      for d in test.elo_diff_pre.values])

    # --- Naive home baseline ---
    base_rate = float(g[g.season >= 2015].home_win.mean())
    p_home = np.full(len(test), base_rate)

    results = {
        'Spread engine (Elo+HCA+rest)': scores(y, p_spread),
        'Elo only': scores(y, p_elo),
        f'Naive home ({base_rate:.1%})': scores(y, p_home),
    }

    # --- Original win-rate classifier ---
    clf_path = ROOT / 'models' / 'logistic.joblib'
    if clf_path.exists():
        df = build_training_frame(games)
        te = df[df.season.isin(HOLDOUT)]
        clf = joblib.load(clf_path)
        p_clf = clf.predict_proba(te[MODEL_COLS])[:, 1]
        results['Win-rate classifier (v1)'] = scores(te.home_win.values, p_clf)

    out = {
        'holdout_seasons': HOLDOUT,
        'metrics': results,
        'reliability_spread_engine': reliability(y, p_spread),
        'coefficients': {
            'home_court_points': eng.hca,
            'points_per_100_elo': round(eng.b_elo * 100, 2),
            'home_b2b_points': eng.home_b2b,
            'away_b2b_points': eng.away_b2b,
            'sigma_points': eng.sigma,
        },
    }
    (ROOT / 'models' / 'metrics_tier1.json').write_text(json.dumps(out, indent=2))

    print(f'Holdout {HOLDOUT}  (n={len(test)})\n')
    print(f'{"model":34s}{"acc":>7}{"logloss":>9}{"brier":>8}')
    for k, v in results.items():
        print(f'{k:34s}{v["accuracy"]:>7.3f}{v["log_loss"]:>9.3f}{v["brier"]:>8.3f}')
    print('\nCalibration (spread engine):')
    print(f'{"pred":>7}{"obs":>7}{"n":>7}')
    for r in out['reliability_spread_engine']:
        print(f'{r["predicted"]:>7.2f}{r["observed"]:>7.2f}{r["n"]:>7}')
    print('\nsaved models/metrics_tier1.json')


if __name__ == '__main__':
    main()
