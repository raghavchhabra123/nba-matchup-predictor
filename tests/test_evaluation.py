from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from scripts.build_ratings import fit_margin_model
from scripts.evaluate import evaluate_window, reliability, scores
from src.elo import compute_elo
from src.features import MODEL_COLS, build_training_frame, add_daily_rank, long_table
from src.ratings import add_rest_flags
from src.validation import temporal_split, validate_games


@pytest.fixture
def games():
    rng = np.random.default_rng(7)
    rows = []
    for season in range(2016, 2026):
        for day in range(20):
            home, away = ('A', 'B') if day % 2 else ('B', 'A')
            hp = int(rng.integers(90, 120))
            rows.append((pd.Timestamp(season, 10, 1) + pd.Timedelta(days=day), season,
                         home, away, hp, 100, int(hp > 100)))
    g = pd.DataFrame(rows, columns=['date','season','home','away','home_pts','away_pts','home_win'])
    g.loc[g.home_pts == 100, 'home_pts'] = 99
    return g


def prepare(g):
    e, _ = compute_elo(g)
    e = add_rest_flags(e)
    e['margin'] = e.home_pts - e.away_pts
    return e, build_training_frame(e)


def test_checked_in_data_contract():
    g = pd.read_csv(Path(__file__).resolve().parents[1] / 'data/games_history.csv', parse_dates=['date'])
    validate_games(g)


@pytest.mark.parametrize('damage', ['duplicate', 'label', 'null', 'tie', 'same_team'])
def test_reject_bad_data(games, damage):
    g = games.copy()
    if damage == 'duplicate': g = pd.concat([g, g.iloc[[0]]])
    elif damage == 'label': g.loc[0, 'home_win'] = 1 - g.loc[0, 'home_win']
    elif damage == 'null': g.loc[0, 'date'] = pd.NaT
    elif damage == 'tie': g.loc[0, 'home_pts'] = g.loc[0, 'away_pts']
    elif damage == 'same_team': g.loc[0, 'away'] = g.loc[0, 'home']
    with pytest.raises(ValueError): validate_games(g)


def test_future_outcomes_cannot_change_past_features(games):
    full, features = prepare(games)
    prefix, prefix_features = prepare(games.iloc[:100])
    assert_frame_equal(full.iloc[:100], prefix)
    assert_frame_equal(features.iloc[:100], prefix_features)
    changed = games.copy()
    changed.loc[100:, ['home_pts', 'away_pts']] = games.loc[100:, ['away_pts', 'home_pts']].values
    changed.loc[100:, 'home_win'] = 1 - games.loc[100:, 'home_win']
    mutated, mutated_features = prepare(changed)
    # Current result cannot influence that game's input either.
    assert_frame_equal(full.loc[:100, ['elo_diff_pre','home_b2b','away_b2b']], mutated.loc[:100, ['elo_diff_pre','home_b2b','away_b2b']])
    assert_frame_equal(features.loc[:100, MODEL_COLS], mutated_features.loc[:100, MODEL_COLS])


def test_split_excludes_later_seasons(games):
    train, test = temporal_split(games, [2023, 2024])
    assert train.season.max() == 2022
    assert test.season.max() == 2024
    with pytest.raises(ValueError): temporal_split(games, [2030])


def test_missing_values_left_for_training_imputer(games):
    frame = build_training_frame(games)
    assert frame.loc[0, MODEL_COLS].isna().any()


def test_holdout_labels_cannot_change_fit_or_baseline(games):
    g, f = prepare(games)
    before, test, pred = evaluate_window(g, f, [2024, 2025])
    changed = games.copy()
    mask = changed.season >= 2024
    changed.loc[mask, ['home_pts','away_pts']] = games.loc[mask, ['away_pts','home_pts']].values
    changed.loc[mask, 'home_win'] = 1 - games.loc[mask, 'home_win']
    g2, f2 = prepare(changed)
    after, _, pred2 = evaluate_window(g2, f2, [2024, 2025])
    assert before['coefficients'] == after['coefficients']
    assert before['baseline_probability'] == after['baseline_probability']
    for name in pred: assert pred[name][0] == pytest.approx(pred2[name][0])


def test_sigma_matches_exported_model(games):
    g, _ = prepare(games)
    train, _ = temporal_split(g, [2024, 2025])
    p = fit_margin_model(train)
    predicted = (p['intercept_hca_points'] + p['b_elo_per_point']*train.elo_diff_pre
                 + p['home_b2b_points']*train.home_b2b + p['away_b2b_points']*train.away_b2b)
    assert p['sigma_points'] == round(float(np.sqrt(np.mean((train.margin-predicted)**2))), 3)


def test_scores_and_reliability():
    s = scores([0, 1], [.25, .75])
    assert s['accuracy'] == 1 and s['brier'] == .0625 and s['roc_auc'] == 1
    assert sum(x['n'] for x in reliability([0, 1], [0., 1.])) == 2
    with pytest.raises(ValueError): scores([1], [np.nan])
    with pytest.raises(ValueError): scores([], [])


def test_standings_include_latest_completed_result_on_idle_days():
    g = pd.DataFrame([
        ('2023-10-01', 2023, 'A', 'B', 1),
        ('2023-10-02', 2023, 'C', 'D', 1),
        ('2023-10-03', 2023, 'B', 'C', 0),
    ], columns=['date','season','home','away','home_win'])
    g.date = pd.to_datetime(g.date)
    tg = add_daily_rank(long_table(g))
    # A and C both won before Oct 3; B lost, so B ranks below both.
    row = tg[(tg.team == 'B') & (tg.date == pd.Timestamp('2023-10-03'))].iloc[0]
    assert row.rank_W_PCT_pre == 3


def test_saved_report_matches_training_fit_and_current_data():
    import hashlib
    import json
    root = Path(__file__).resolve().parents[1]
    path = root / 'data/games_history.csv'
    saved = json.loads((root / 'models/metrics_tier1.json').read_text())
    engine = json.loads((root / 'models/engine.json').read_text())
    g, f = prepare(pd.read_csv(path, parse_dates=['date']))
    rebuilt, _, _ = evaluate_window(g, f, saved['holdout_seasons'])
    assert saved['data_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert saved['metrics'] == rebuilt['metrics']
    assert saved['coefficients'] == rebuilt['coefficients']
    for name, value in rebuilt['coefficients'].items():
        assert engine[name] == pytest.approx(value)
