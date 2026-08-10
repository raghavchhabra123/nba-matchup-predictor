"""Train win-probability models on 2003-2026 games with a chronological split.

Usage:  python -m scripts.train_model   (run from the project root)
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features import MODEL_COLS, build_training_frame, team_snapshot  # noqa: E402

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (accuracy_score, brier_score_loss,  # noqa: E402
                             roc_auc_score)
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

TEST_SEASONS = [2024, 2025]  # 2024-25 and 2025-26 held out


def make_models():
    models = {
        'Logistic Regression': make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)),
    }
    if HAS_XGB:
        models['XGBoost'] = XGBClassifier(
            n_estimators=400, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, reg_lambda=2.0,
            eval_metric='logloss', random_state=42)
    return models


def main():
    games = pd.read_csv(ROOT / 'data' / 'games_history.csv', parse_dates=['date'])
    df = build_training_frame(games)

    train = df[~df.season.isin(TEST_SEASONS)]
    test = df[df.season.isin(TEST_SEASONS)]
    Xtr, ytr = train[MODEL_COLS], train.home_win
    Xte, yte = test[MODEL_COLS], test.home_win
    print(f'train {len(train)} games (seasons {train.season.min()}-{train.season.max()}), '
          f'test {len(test)}')

    metrics = {}
    for name, model in make_models().items():
        model.fit(Xtr, ytr)
        p = model.predict_proba(Xte)[:, 1]
        metrics[name] = {
            'accuracy': round(accuracy_score(yte, p > 0.5), 4),
            'roc_auc': round(roc_auc_score(yte, p), 4),
            'brier': round(brier_score_loss(yte, p), 4),
        }
        print(name, metrics[name])

    # Refit on everything for deployment
    (ROOT / 'models').mkdir(exist_ok=True)
    for name, model in make_models().items():
        model.fit(df[MODEL_COLS], df.home_win)
        fname = 'xgboost.joblib' if 'XG' in name else 'logistic.joblib'
        joblib.dump(model, ROOT / 'models' / fname)

    home_win_rate = float(df[df.season >= 2015].home_win.mean())
    meta = {
        'metrics_holdout_2024_2026': metrics,
        'test_seasons': TEST_SEASONS,
        'n_games_total': int(len(df)),
        'league_home_win_rate_since_2015': round(home_win_rate, 4),
        'features': MODEL_COLS,
    }
    (ROOT / 'models' / 'metrics.json').write_text(json.dumps(meta, indent=2))

    snap = team_snapshot(games)
    snap.to_csv(ROOT / 'data' / 'team_snapshot_2026.csv', index=False)
    print('saved models/, data/team_snapshot_2026.csv')


if __name__ == '__main__':
    main()
