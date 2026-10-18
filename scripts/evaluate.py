"""Reproducible chronological evaluation; never loads deployment estimators.

Run python -m scripts.evaluate. Elo updates after each completed game while
fitted coefficients and imputation remain frozen for each evaluation window.
"""
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scripts.build_ratings import fit_margin_model
from src.elo import HCA_ELO, compute_elo, win_prob_from_elo
from src.engine import _phi
from src.features import MODEL_COLS, build_training_frame
from src.ratings import add_rest_flags
from src.validation import temporal_split, validate_games

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT = [2024, 2025]


def scores(y, p):
    y, p = np.asarray(y), np.asarray(p)
    if y.ndim != 1 or p.shape != y.shape or not len(y):
        raise ValueError('Expected nonempty aligned one-dimensional arrays')
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid labels or probabilities')
    clipped = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        'accuracy': round(float(((p > .5) == y).mean()), 4),
        'log_loss': round(float(-(y * np.log(clipped) + (1-y) * np.log(1-clipped)).mean()), 4),
        'brier': round(float(((p-y)**2).mean()), 4),
        'roc_auc': round(float(roc_auc_score(y, p)), 4) if len(np.unique(y)) == 2 else None,
        'average_precision': round(float(average_precision_score(y, p)), 4) if y.sum() else None,
        'n': int(len(y)),
    }


def reliability(y, p, bins=10):
    y, p = np.asarray(y), np.asarray(p)
    out = []
    edges = np.linspace(0, 1, bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if m.any():
            out.append(dict(bin=round((lo+hi)/2, 2), predicted=round(float(p[m].mean()), 4),
                            observed=round(float(y[m].mean()), 4), n=int(m.sum())))
    return out


def evaluate_window(g, features, seasons):
    train, test = temporal_split(g, seasons)
    params = fit_margin_model(train)
    margin = (params['intercept_hca_points'] + params['b_elo_per_point'] * test.elo_diff_pre
              + params['home_b2b_points'] * test.home_b2b + params['away_b2b_points'] * test.away_b2b)
    baseline_train = train[train.season >= 2015]
    if baseline_train.empty:
        raise ValueError('Baseline needs training games from 2015 onward')
    base_rate = float(baseline_train.home_win.mean())
    ft, fe = temporal_split(features, seasons)
    clf = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                        LogisticRegression(C=1., max_iter=2000, random_state=42))
    clf.fit(ft[MODEL_COLS], ft.home_win)
    if not test[['date', 'home', 'away']].reset_index(drop=True).equals(fe[['date', 'home', 'away']].reset_index(drop=True)):
        raise ValueError('Classifier and engine evaluation games differ')
    predictions = {
        'Spread engine (Elo+HCA+rest)': np.array([_phi(m / params['sigma_points']) for m in margin]),
        'Elo only': np.array([win_prob_from_elo(d, HCA_ELO) for d in test.elo_diff_pre]),
        'Training home-rate baseline': np.full(len(test), base_rate),
        'Win-rate logistic (train-only)': clf.predict_proba(fe[MODEL_COLS])[:, 1],
    }
    result = {
        'train_seasons': [int(train.season.min()), int(train.season.max())],
        'test_seasons': seasons,
        'train_last_date': str(train.date.max().date()),
        'test_first_date': str(test.date.min().date()),
        'baseline_probability': base_rate,
        'baseline_training_n': len(baseline_train),
        'metrics': {name: scores(test.home_win, p) for name, p in predictions.items()},
        'coefficients': params,
    }
    return result, test, predictions


def paired_date_bootstrap(test, predictions, draws=2000):
    """Paired resampling of dates, retaining within-day game dependence."""
    y = test.home_win.to_numpy()
    a = predictions['Spread engine (Elo+HCA+rest)']
    b = predictions['Elo only']
    delta = ((a > .5) == y).astype(float) - ((b > .5) == y).astype(float)
    daily = pd.DataFrame({'date': test.date.values, 'delta': delta}).groupby('date').delta.agg(['sum', 'count'])
    rng = np.random.default_rng(42)
    idx = rng.integers(0, len(daily), size=(draws, len(daily)))
    draws_delta = daily['sum'].to_numpy()[idx].sum(axis=1) / daily['count'].to_numpy()[idx].sum(axis=1)
    return {'accuracy_difference': float(delta.mean()),
            'ci_95': np.quantile(draws_delta, [.025, .975]).tolist(),
            'draws': draws, 'seed': 42, 'unit': 'game date',
            'limitation': 'Does not account for dependence across dates or model-selection uncertainty.'}


def main():
    path = ROOT / 'data/games_history.csv'
    games = pd.read_csv(path, parse_dates=['date'])
    validate_games(games)
    g, _ = compute_elo(games)
    g = add_rest_flags(g)
    g['margin'] = g.home_pts - g.away_pts
    features = build_training_frame(g)
    out, test, predictions = evaluate_window(g, features, HOLDOUT)
    out['holdout_seasons'] = HOLDOUT
    out['protocol'] = 'Frozen fitted parameters; sequential pre-game Elo updated after completed games. Retrospective evaluation, not a pristine model-selection holdout.'
    out['data_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    out['environment'] = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'scikit_learn': sklearn.__version__}
    out['reliability_spread_engine'] = reliability(test.home_win, predictions['Spread engine (Elo+HCA+rest)'])
    out['paired_spread_vs_elo'] = paired_date_bootstrap(test, predictions)
    out['per_season'] = {str(season): {name: scores(test.loc[test.season == season, 'home_win'], p[(test.season == season).values]) for name, p in predictions.items()} for season in HOLDOUT}
    out['rolling_origin_development'] = [evaluate_window(g, features, [s])[0] for s in [2021, 2022, 2023]]
    (ROOT / 'models/metrics_tier1.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    pred = test[['date', 'season', 'home', 'away', 'home_win']].copy()
    for name, p in predictions.items():
        pred[name] = p
    (ROOT / 'reports').mkdir(exist_ok=True)
    pred.to_csv(ROOT / 'reports/holdout_predictions.csv', index=False)
    print(json.dumps(out['metrics'], indent=2))
    print('Paired accuracy difference vs Elo:', out['paired_spread_vs_elo'])


if __name__ == '__main__':
    main()
