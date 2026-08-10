"""Live data refresh via nba_api (stats.nba.com). Free, no API key.

Called from the app's "Refresh live data" button. Falls back silently if
stats.nba.com is unreachable (it blocks some networks / cloud IPs).
Refreshed CSVs are written to data/live/ and preferred over the bundled
snapshot when present.
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LIVE_DIR = ROOT / 'data' / 'live'


def current_season_str(today=None) -> str:
    today = today or datetime.now()
    y = today.year if today.month >= 10 else today.year - 1
    return f'{y}-{str(y + 1)[2:]}'


def fetch_games(season: str) -> pd.DataFrame:
    """Regular-season games as: date, season, home, away, home_pts, away_pts, home_win."""
    from nba_api.stats.endpoints import leaguegamefinder
    lg = leaguegamefinder.LeagueGameFinder(
        season_nullable=season, season_type_nullable='Regular Season',
        league_id_nullable='00', timeout=20).get_data_frames()[0]
    lg['GAME_DATE'] = pd.to_datetime(lg.GAME_DATE)
    lg = lg[lg.WL.notna()]
    home = lg[lg.MATCHUP.str.contains('vs.')]
    away = lg[lg.MATCHUP.str.contains('@')][['GAME_ID', 'TEAM_ABBREVIATION', 'PTS']]
    g = home.merge(away, on='GAME_ID', suffixes=('', '_A'))
    return pd.DataFrame({
        'date': g.GAME_DATE, 'season': int(season[:4]),
        'home': g.TEAM_ABBREVIATION, 'away': g.TEAM_ABBREVIATION_A,
        'home_pts': g.PTS, 'away_pts': g.PTS_A,
        'home_win': (g.WL == 'W').astype(int),
    }).sort_values('date').reset_index(drop=True)


def fetch_players(season: str) -> pd.DataFrame:
    """Per-player season stats + a BPM-style impact (points/100 above average).

    Uses published Basketball-Reference BPM for anchor players and a calibrated
    box-score + on-court plus/minus estimate for everyone else, matching
    scripts/build_players.py so the live and bundled data are consistent.
    """
    import numpy as np
    from nba_api.stats.endpoints import leaguedashplayerstats

    from src.bpm_anchors import BPM_ANCHORS
    ps = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed='PerGame', timeout=20).get_data_frames()[0]
    ps = ps[(ps.GP >= 8) & (ps.MIN > 0)].copy()
    gmsc_pg = (ps.PTS + 0.4 * ps.FGM - 0.7 * ps.FGA - 0.4 * (ps.FTA - ps.FTM)
               + 0.7 * ps.OREB + 0.3 * ps.DREB + ps.STL + 0.7 * ps.AST
               + 0.7 * ps.BLK - 0.4 * ps.PF - ps.TOV)
    min_total = ps.MIN * ps.GP
    pm_per100 = (ps.PLUS_MINUS * ps.GP / (min_total * (99.0 / 48.0))) * 100
    shrink = min_total / (min_total + 600)
    gmsc36 = 36 * gmsc_pg / ps.MIN
    raw = 0.55 * (pm_per100 * shrink) + 0.45 * ((gmsc36 - 10.0) * 0.7)

    names = ps.PLAYER_NAME
    anchor = names.map(BPM_ANCHORS)
    cal = anchor.notna()
    if cal.sum() >= 5:
        A = np.column_stack([np.ones(cal.sum()), raw[cal].values])
        b, *_ = np.linalg.lstsq(A, anchor[cal].values, rcond=None)
        bpm = b[0] + b[1] * raw
    else:
        bpm = raw
    bpm = np.where(anchor.notna(), anchor, bpm)
    bpm = pd.Series(bpm, index=ps.index).clip(-6, 15).round(2)

    out = pd.DataFrame({
        'athlete_id': ps.PLAYER_ID, 'athlete_display_name': ps.PLAYER_NAME,
        'team': ps.TEAM_ABBREVIATION, 'pos': '', 'headshot': '',
        'gp': ps.GP, 'min_pg': ps.MIN, 'pts_pg': ps.PTS,
        'reb_pg': ps.REB, 'ast_pg': ps.AST,
        'bpm': bpm, 'impact': (bpm * (ps.MIN / 48.0)).round(2),
    })
    return out[out.gp >= 8].sort_values('bpm', ascending=False).round(2)


def refresh(season: str | None = None) -> dict:
    """Fetch fresh season data; write to data/live/. Raises on network failure."""
    import sys
    sys.path.insert(0, str(ROOT))
    from src.features import team_snapshot

    season = season or current_season_str()
    games = fetch_games(season)
    players = fetch_players(season)
    if games.empty:
        raise RuntimeError(f'No completed games returned for {season}')
    snap = team_snapshot(games)
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    games.to_csv(LIVE_DIR / 'games.csv', index=False)
    players.to_csv(LIVE_DIR / 'players.csv', index=False)
    snap.to_csv(LIVE_DIR / 'team_snapshot.csv', index=False)
    (LIVE_DIR / 'meta.txt').write_text(
        f'{season}|{datetime.now().isoformat(timespec="seconds")}|{len(games)}')
    return {'season': season, 'games': len(games), 'players': len(players)}
