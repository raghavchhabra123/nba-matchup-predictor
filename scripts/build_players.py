"""Build data/players_2026.csv with a BPM-style impact for every player.

Impact metric = Box Plus/Minus (points per 100 possessions above league
average). For star players we use the published Basketball-Reference BPM
directly (BPM_ANCHORS); for everyone else we estimate BPM from the complete
hoopR box-score + on-court plus/minus data and calibrate its scale so the
estimate matches the published anchors. Replacement level = -2.0 (BBRef).

Run:  python -m scripts.build_players     (needs the hoopR clone at HOOPR)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.bpm_anchors import BPM_ANCHORS  # noqa: E402

HOOPR = Path('/tmp/hoopr/nba/player_box/parquet/player_box_2026.parquet')
REPLACEMENT_BPM = -2.0

TEAM_FIX = {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS',
            'UTAH': 'UTA', 'WSH': 'WAS'}


def game_score(d):
    return (d.points + 0.4 * d.field_goals_made - 0.7 * d.field_goals_attempted
            - 0.4 * (d.free_throws_attempted - d.free_throws_made)
            + 0.7 * d.offensive_rebounds + 0.3 * d.defensive_rebounds
            + d.steals + 0.7 * d.assists + 0.7 * d.blocks
            - 0.4 * d.fouls - d.turnovers)


def main():
    pb = pd.read_parquet(HOOPR)
    pb = pb[(pb.season_type == 2) & (~pb.did_not_play)
            & pb.minutes.notna() & (pb.minutes > 0)].copy()
    pb['team_abbreviation'] = pb.team_abbreviation.replace(TEAM_FIX)
    pb['gmsc'] = game_score(pb)
    pb['pm'] = pd.to_numeric(pb.plus_minus, errors='coerce')

    agg = pb.groupby(['athlete_id', 'athlete_display_name']).agg(
        team=('team_abbreviation', lambda x: x.iloc[-1]),
        pos=('athlete_position_abbreviation', 'last'),
        headshot=('athlete_headshot_href', 'last'),
        gp=('game_id', 'nunique'), min_total=('minutes', 'sum'),
        pts_pg=('points', 'mean'), reb_pg=('rebounds', 'mean'),
        ast_pg=('assists', 'mean'),
        pm_total=('pm', 'sum'), gmsc_total=('gmsc', 'sum'),
    ).reset_index()
    agg = agg[agg.gp >= 8].copy()
    agg['min_pg'] = agg.min_total / agg.gp

    # --- estimate BPM (pts/100) from box score + on-court plus/minus ---
    poss_per_min = 99.0 / 48.0
    pm_per100 = (agg.pm_total / (agg.min_total * poss_per_min)) * 100
    shrink = agg.min_total / (agg.min_total + 600)          # tame small samples
    gmsc36 = 36 * agg.gmsc_total / agg.min_total
    box_component = (gmsc36 - 10.0) * 0.7                   # ~0 for a league-average scorer
    est = 0.55 * (pm_per100 * shrink) + 0.45 * box_component

    # calibrate est to the published anchors via least-squares (est -> BPM)
    agg['bpm_est_raw'] = est
    key = agg.athlete_display_name.map(BPM_ANCHORS)
    cal = agg[key.notna()]
    if len(cal) >= 5:
        A = np.column_stack([np.ones(len(cal)), cal.bpm_est_raw.values])
        b, *_ = np.linalg.lstsq(A, key[key.notna()].values, rcond=None)
        agg['bpm'] = b[0] + b[1] * agg.bpm_est_raw
        print(f'calibration: BPM = {b[0]:+.2f} + {b[1]:.2f}*raw  '
              f'(anchors n={len(cal)})')
    else:
        agg['bpm'] = agg.bpm_est_raw

    # override with published BPM where available
    agg['bpm'] = agg.apply(
        lambda r: BPM_ANCHORS.get(r.athlete_display_name, r.bpm), axis=1)
    agg['is_anchor'] = agg.athlete_display_name.isin(BPM_ANCHORS)

    # --- recenter non-anchor players so each team's minutes-weighted BPM
    #     matches its ACTUAL net rating (identity: net ≈ Σ BPM·min/48).
    #     Keeps published stars fixed; ties bench value to real results. ---
    ratings = pd.read_csv(ROOT / 'data' / 'elo_ratings_2026.csv')
    net = dict(zip(ratings.team, ratings.net_rating))
    for team, grp in agg.groupby('team'):
        rot = grp.sort_values('min_pg', ascending=False).head(10)
        if rot.empty or team not in net or pd.isna(net[team]):
            continue
        w = rot.min_pg * (240.0 / rot.min_pg.sum()) / 48.0   # weights sum to 5
        implied = float((rot.bpm.values * w.values).sum())
        na = ~rot.is_anchor.values
        wsum = float(w.values[na].sum())
        if wsum > 0.5:
            shift = np.clip((net[team] - implied) / wsum, -7, 3)
            agg.loc[rot.index[na], 'bpm'] = agg.loc[rot.index[na], 'bpm'] + shift
    agg['bpm'] = agg.bpm.clip(-6, 15).round(2)

    # legacy points-per-game impact (for display / backward compat)
    agg['impact'] = (agg.bpm * (agg.min_pg / 48.0)).round(2)

    cols = ['athlete_id', 'athlete_display_name', 'team', 'pos', 'headshot',
            'gp', 'min_pg', 'pts_pg', 'reb_pg', 'ast_pg', 'bpm', 'impact']
    out = agg[cols].sort_values('bpm', ascending=False).round(2)
    out.to_csv(ROOT / 'data' / 'players_2026.csv', index=False)

    print(f'\nsaved {len(out)} players -> data/players_2026.csv')
    print('\nTop 8 by BPM:')
    for r in out.head(8).itertuples():
        print(f'  {r.athlete_display_name:26s} {r.team:4s} BPM {r.bpm:+5.1f}  '
              f'{r.min_pg:.0f} min  (pts/gm impact {r.impact:+.1f})')
    # quick anchor check
    chk = out[out.athlete_display_name.isin(['Nikola Jokić', 'Nikola Jokic'])]
    print('\nanchor spot-check (Jokic should be ~14.2):',
          chk.bpm.values if len(chk) else 'not found')


if __name__ == '__main__':
    sys.exit(main())
