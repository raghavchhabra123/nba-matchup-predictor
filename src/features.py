"""Leak-free feature engineering, mirroring the original notebook pipeline.

Features (15), identical to PredictNBAHomeGamesProject.ipynb:
  H_/A_ win_rate_last10, win_rate_season, rest_days, home_rate_last10,
  rank_W_PCT_pre  + the 5 home-minus-away diffs.
"""
import numpy as np
import pandas as pd

MODEL_COLS = [
    'H_win_rate_last10', 'A_win_rate_last10', 'diff_win_rate_last10',
    'H_win_rate_season', 'A_win_rate_season', 'diff_win_rate_season',
    'H_rest_days', 'A_rest_days', 'diff_rest_days',
    'H_home_rate_last10', 'A_home_rate_last10', 'diff_home_rate_last10',
    'H_rank_W_PCT_pre', 'A_rank_W_PCT_pre', 'diff_rank_W_PCT_pre',
]


def _shifted_rolling_mean(s: pd.Series, window: int, minp: int = 1) -> pd.Series:
    return s.shift(1).rolling(window=window, min_periods=minp).mean()


def long_table(games: pd.DataFrame) -> pd.DataFrame:
    """games: date, season, home, away, home_win -> one row per team-game."""
    h = pd.DataFrame({'date': games.date, 'season': games.season, 'game_idx': games.index,
                      'team': games.home, 'is_home': True, 'win': games.home_win})
    a = pd.DataFrame({'date': games.date, 'season': games.season, 'game_idx': games.index,
                      'team': games.away, 'is_home': False, 'win': 1 - games.home_win})
    tg = pd.concat([h, a]).sort_values(['team', 'date']).reset_index(drop=True)

    grp = tg.groupby(['team', 'season'], sort=False)
    tg['win_rate_last10'] = grp['win'].transform(lambda s: _shifted_rolling_mean(s, 10, 3))
    tg['win_rate_season'] = grp['win'].transform(lambda s: s.shift(1).expanding().mean())
    tg['home_rate_last10'] = grp['is_home'].transform(lambda s: _shifted_rolling_mean(s.astype(float), 10, 3))
    tg['rest_days'] = tg.groupby('team')['date'].transform(lambda s: s.diff().dt.days).clip(upper=14)
    return tg


def add_daily_rank(tg: pd.DataFrame) -> pd.DataFrame:
    """Pre-game league rank (1=best) by cumulative season win%, per day."""
    out = []
    for season, sdf in tg.groupby('season'):
        pivot = (sdf.pivot_table(index='date', columns='team',
                                 values='win_rate_season', aggfunc='last')
                    .ffill())
        rank = pivot.rank(axis=1, ascending=False, method='min')
        r = rank.stack().rename('rank_W_PCT_pre').reset_index()
        r['season'] = season
        out.append(r)
    ranks = pd.concat(out)
    return tg.merge(ranks, on=['season', 'date', 'team'], how='left')


def build_training_frame(games: pd.DataFrame) -> pd.DataFrame:
    games = games.reset_index(drop=True)
    tg = add_daily_rank(long_table(games))
    cols = ['game_idx', 'win_rate_last10', 'win_rate_season', 'rest_days',
            'home_rate_last10', 'rank_W_PCT_pre']
    hf = tg[tg.is_home][cols].rename(columns={c: 'H_' + c for c in cols[1:]})
    af = tg[~tg.is_home][cols].rename(columns={c: 'A_' + c for c in cols[1:]})
    df = (games[['date', 'season', 'home', 'away', 'home_win']]
          .reset_index().rename(columns={'index': 'game_idx'})
          .merge(hf, on='game_idx').merge(af, on='game_idx'))
    for f in ['win_rate_last10', 'win_rate_season', 'rest_days',
              'home_rate_last10', 'rank_W_PCT_pre']:
        df[f'diff_{f}'] = df[f'H_{f}'] - df[f'A_{f}']
    df = df.rename(columns={'diff_rank_W_PCT_pre': 'diff_rank_W_PCT_pre'})
    df[MODEL_COLS] = df[MODEL_COLS].fillna(df[MODEL_COLS].median())
    return df


def team_snapshot(games: pd.DataFrame) -> pd.DataFrame:
    """End-of-data team state (INCLUDING last game) for predicting a future matchup."""
    games = games.reset_index(drop=True)
    last_season = games.season.max()
    g = games[games.season == last_season]
    tg = long_table(g)
    rows = []
    for team, tdf in tg.groupby('team'):
        tdf = tdf.sort_values('date')
        rows.append({
            'team': team,
            'win_rate_last10': tdf.win.tail(10).mean(),
            'win_rate_season': tdf.win.mean(),
            'home_rate_last10': 0.5,  # unknown for a hypothetical future game
            'wins': int(tdf.win.sum()), 'losses': int((1 - tdf.win).sum()),
            'last_game': tdf.date.max().date().isoformat(),
        })
    snap = pd.DataFrame(rows)
    snap['rank_W_PCT'] = snap.win_rate_season.rank(ascending=False, method='min')
    snap['season'] = last_season
    return snap.sort_values('rank_W_PCT').reset_index(drop=True)


def matchup_features(home_row, away_row, home_rest: float = 2, away_rest: float = 2) -> pd.DataFrame:
    """One-row feature frame for home_row (team snapshot) hosting away_row."""
    d = {
        'H_win_rate_last10': home_row.win_rate_last10, 'A_win_rate_last10': away_row.win_rate_last10,
        'H_win_rate_season': home_row.win_rate_season, 'A_win_rate_season': away_row.win_rate_season,
        'H_rest_days': home_rest, 'A_rest_days': away_rest,
        'H_home_rate_last10': home_row.home_rate_last10, 'A_home_rate_last10': away_row.home_rate_last10,
        'H_rank_W_PCT_pre': home_row.rank_W_PCT, 'A_rank_W_PCT_pre': away_row.rank_W_PCT,
    }
    for f in ['win_rate_last10', 'win_rate_season', 'rest_days', 'home_rate_last10']:
        d[f'diff_{f}'] = d[f'H_{f}'] - d[f'A_{f}']
    d['diff_rank_W_PCT_pre'] = d['H_rank_W_PCT_pre'] - d['A_rank_W_PCT_pre']
    return pd.DataFrame([d])[MODEL_COLS]
