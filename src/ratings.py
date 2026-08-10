"""Shared helpers: rest/back-to-back flags, rolling net rating, and the
point-spread margin model spec used by both training and the live app.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_rest_flags(games: pd.DataFrame) -> pd.DataFrame:
    """Add home_rest, away_rest (days since last game, capped 5) and B2B flags."""
    g = games.sort_values('date').reset_index(drop=True).copy()
    long = pd.concat([
        g[['date', 'home']].rename(columns={'home': 'team'}),
        g[['date', 'away']].rename(columns={'away': 'team'}),
    ]).sort_values(['team', 'date'])
    long['rest'] = long.groupby('team')['date'].diff().dt.days
    rest_map = {}
    for r in long.itertuples():
        rest_map[(r.team, r.date)] = r.rest
    g['home_rest'] = [rest_map.get((h, d), np.nan) for h, d in zip(g.home, g.date)]
    g['away_rest'] = [rest_map.get((a, d), np.nan) for a, d in zip(g.away, g.date)]
    for c in ['home_rest', 'away_rest']:
        g[c] = g[c].clip(upper=5)
    g['home_b2b'] = (g['home_rest'] == 1).astype(int)
    g['away_b2b'] = (g['away_rest'] == 1).astype(int)
    return g


def add_net_rating(games: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Shifted rolling point differential per team (leak-free) -> diff column."""
    g = games.sort_values('date').reset_index(drop=True).copy()
    h = pd.DataFrame({'date': g.date, 'season': g.season, 'idx': g.index,
                      'team': g.home, 'margin': g.home_pts - g.away_pts})
    a = pd.DataFrame({'date': g.date, 'season': g.season, 'idx': g.index,
                      'team': g.away, 'margin': g.away_pts - g.home_pts})
    tg = pd.concat([h, a]).sort_values(['team', 'date'])
    tg['nr'] = (tg.groupby(['team', 'season'])['margin']
                .transform(lambda s: s.shift(1).rolling(window, min_periods=5).mean()))
    nr = dict(zip(zip(tg.team, tg.idx), tg.nr))
    g['home_nr'] = [nr.get((t, i), np.nan) for t, i in zip(g.home, g.index)]
    g['away_nr'] = [nr.get((t, i), np.nan) for t, i in zip(g.away, g.index)]
    g['net_rtg_diff'] = g['home_nr'] - g['away_nr']
    return g


# Feature columns fed to the margin regression (point-spread backbone).
MARGIN_FEATURES = ['elo_diff_pre', 'home_b2b', 'away_b2b']
