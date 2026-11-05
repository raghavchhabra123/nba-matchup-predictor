"""Current-season tracking: results, frozen-model predictions, and a live scorecard.

Design rules (agreed with reviewers before implementation):

* Results and predictions live in separate tables. Results (``games.csv``) are
  an upsert of the latest feed state per ESPN event ID. Predictions
  (``predictions.csv``) are append-only and never rewritten.
* A prediction is made only before tip-off. A run that arrives after tip-off
  (minus a safety buffer) records the game in ``missed.csv`` instead of
  producing a retrospective prediction.
* Ratings are always rebuilt by replaying every completed game in order, so
  off-season regression is applied exactly once per season, re-runs are
  idempotent, and score corrections flow through without touching old
  predictions.
* Prospective eligibility needs proof the prediction was *published* before
  tip-off. A local timestamp is not proof. See ``eligibility`` below.
* The scorecard model is the frozen base engine (Elo + home court + rest).
  Roster projections and travel adjustments are scenario features and are
  never scored here.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.elo import BASE, CARRYOVER, HCA_ELO, K0, MEAN, compute_elo

ROOT = Path(__file__).resolve().parents[1]
SEASON_DIR = ROOT / 'data' / 'season'
ET = ZoneInfo('America/New_York')

SCOREBOARD_URL = ('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/'
                  'scoreboard?dates={yyyymmdd}')

# ESPN abbreviations that differ from the ones used throughout this repo.
ESPN_TO_REPO = {'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK', 'SA': 'SAS',
                'UTAH': 'UTA', 'WSH': 'WAS'}
TEAMS = {'ATL', 'BKN', 'BOS', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW',
         'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK',
         'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS'}

STATUS_MAP = {'STATUS_FINAL': 'final', 'STATUS_SCHEDULED': 'scheduled',
              'STATUS_POSTPONED': 'postponed', 'STATUS_CANCELED': 'canceled',
              'STATUS_IN_PROGRESS': 'in_progress', 'STATUS_HALFTIME': 'in_progress',
              'STATUS_END_PERIOD': 'in_progress', 'STATUS_DELAYED': 'scheduled',
              'STATUS_SUSPENDED': 'postponed'}

PREDICT_HORIZON = timedelta(hours=24)   # predict games tipping off within this window
TIPOFF_BUFFER = timedelta(minutes=10)    # must be published at least this early
RESCHEDULE_TOLERANCE = timedelta(hours=3)  # bigger tipoff shift voids a prediction
RECHECK_DAYS = 7                         # re-read recent days for corrections

GAME_COLS = ['event_id', 'season', 'tipoff_utc', 'status', 'home', 'away',
             'home_pts', 'away_pts', 'neutral']
PRED_COLS = ['event_id', 'home', 'away', 'neutral', 'tipoff_utc', 'predicted_at_utc',
             'data_cutoff_utc', 'p_home', 'margin', 'elo_home', 'elo_away',
             'home_b2b', 'away_b2b', 'model_version', 'code_version', 'run_id']
MISSED_COLS = ['event_id', 'home', 'away', 'tipoff_utc', 'noticed_at_utc', 'run_id',
               'reason']
RECEIPT_COLS = ['run_id', 'conclusion', 'completed_at_utc', 'head_sha', 'checked_at_utc']


class FeedError(RuntimeError):
    """The schedule/results feed failed or returned data we will not trust."""


# --------------------------------------------------------------------------- utils
def iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_ts(s: str) -> datetime:
    dt = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def et_date(tipoff_utc: str) -> pd.Timestamp:
    """Calendar date in US Eastern — matches how games_history.csv dates games."""
    return pd.Timestamp(parse_ts(tipoff_utc).astimezone(ET).date())


def season_of(tipoff: datetime) -> int:
    """Season label as used in this repo: start year (2026-27 season -> 2026)."""
    d = tipoff.astimezone(ET)
    return d.year if d.month >= 8 else d.year - 1


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# --------------------------------------------------------------------------- feed
def parse_scoreboard(payload: dict) -> list[dict]:
    """ESPN scoreboard JSON -> raw event dicts (regular season only)."""
    if not isinstance(payload, dict) or 'events' not in payload:
        raise FeedError('scoreboard payload has no "events" key')
    out = []
    for e in payload['events']:
        if (e.get('season') or {}).get('type') != 2:      # 1 = pre, 3 = post
            continue
        c = e['competitions'][0]
        h = next(x for x in c['competitors'] if x['homeAway'] == 'home')
        a = next(x for x in c['competitors'] if x['homeAway'] == 'away')
        out.append({'id': str(e['id']), 'date': c.get('date') or e['date'],
                    'status': e['status']['type']['name'],
                    'home': h['team']['abbreviation'], 'away': a['team']['abbreviation'],
                    'home_score': h.get('score'), 'away_score': a.get('score'),
                    'neutral': bool(c.get('neutralSite'))})
    return out


def fetch_events(dates, get_json=None) -> list[dict]:
    """Fetch and parse the scoreboard for each date. Any failure raises FeedError,
    so the caller can keep the last valid data instead of writing a partial state."""
    if get_json is None:
        import requests

        def get_json(url):
            r = requests.get(url, timeout=20, headers={'User-Agent': 'nba-matchup-predictor'})
            r.raise_for_status()
            return r.json()
    events = []
    for d in dates:
        url = SCOREBOARD_URL.format(yyyymmdd=pd.Timestamp(d).strftime('%Y%m%d'))
        try:
            events.extend(parse_scoreboard(get_json(url)))
        except FeedError:
            raise
        except Exception as exc:                       # network, JSON, schema
            raise FeedError(f'{type(exc).__name__} fetching {url}: {exc}') from exc
    return events


def normalize(raw_events: list[dict]) -> pd.DataFrame:
    """Raw events -> validated games table. Raises FeedError on anything suspect."""
    rows = []
    for e in raw_events:
        status = STATUS_MAP.get(e['status'])
        if status is None:
            raise FeedError(f"unknown status {e['status']!r} for event {e['id']}")
        home = ESPN_TO_REPO.get(e['home'], e['home'])
        away = ESPN_TO_REPO.get(e['away'], e['away'])
        if home not in TEAMS or away not in TEAMS or home == away:
            raise FeedError(f"bad teams {e['home']!r} vs {e['away']!r} in {e['id']}")
        tip = parse_ts(e['date'])
        hp = ap = np.nan
        if status == 'final':
            try:
                hp, ap = int(e['home_score']), int(e['away_score'])
            except (TypeError, ValueError):
                raise FeedError(f"final {e['id']} has non-numeric score")
            if hp == ap or min(hp, ap) < 40 or max(hp, ap) > 200:
                raise FeedError(f"implausible final {hp}-{ap} in {e['id']}")
        rows.append({'event_id': str(e['id']), 'season': season_of(tip),
                     'tipoff_utc': iso(tip), 'status': status, 'home': home,
                     'away': away, 'home_pts': hp, 'away_pts': ap,
                     'neutral': int(bool(e['neutral']))})
    df = pd.DataFrame(rows, columns=GAME_COLS)
    # The same event can appear on two date pages around midnight; keep one.
    return df.drop_duplicates('event_id', keep='last').reset_index(drop=True)


# --------------------------------------------------------------------------- store
def _read(path: Path, cols) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path, dtype={'event_id': str, 'run_id': str})
        return df[cols] if set(cols) <= set(df.columns) else df
    return pd.DataFrame(columns=cols)


def _mask(bools) -> np.ndarray:
    """Row mask that stays a row mask when empty (df[[]] would select columns)."""
    return np.fromiter(bools, dtype=bool)


def _cat(a: pd.DataFrame, b: pd.DataFrame, cols) -> pd.DataFrame:
    parts = [x[cols] for x in (a, b) if len(x)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)


def _write(df: pd.DataFrame, path: Path, sort) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(sort, kind='mergesort').to_csv(path, index=False)


@dataclass
class Store:
    root: Path = SEASON_DIR

    @property
    def games_path(self): return self.root / 'games.csv'
    @property
    def preds_path(self): return self.root / 'predictions.csv'
    @property
    def missed_path(self): return self.root / 'missed.csv'
    @property
    def receipts_path(self): return self.root / 'run_receipts.csv'
    @property
    def status_path(self): return self.root / 'status.json'

    def games(self): return _read(self.games_path, GAME_COLS)
    def preds(self): return _read(self.preds_path, PRED_COLS)
    def missed(self): return _read(self.missed_path, MISSED_COLS)
    def receipts(self): return _read(self.receipts_path, RECEIPT_COLS)

    def status(self) -> dict:
        return json.loads(self.status_path.read_text()) if self.status_path.exists() else {}


def merge_games(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Latest feed state wins per event ID (handles corrections and reschedules)."""
    both = pd.concat([df for df in (old, new) if len(df)], ignore_index=True) \
        if len(old) or len(new) else new.copy()
    both['event_id'] = both['event_id'].astype(str)
    return both.drop_duplicates('event_id', keep='last').reset_index(drop=True)


# --------------------------------------------------------------------------- model
def load_engine(path: Path | None = None) -> dict:
    return json.loads(Path(path or ROOT / 'models' / 'engine.json').read_text())


def model_version(engine: dict) -> str:
    """Fingerprint of everything that determines a prediction."""
    keys = ['intercept_hca_points', 'b_elo_per_point', 'home_b2b_points',
            'away_b2b_points', 'sigma_points']
    spec = {k: engine[k] for k in keys}
    spec.update({'elo': {'base': BASE, 'mean': MEAN, 'carryover': CARRYOVER,
                         'hca_elo': HCA_ELO, 'k0': K0}})
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]


def history_with_season(history: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Historical games + completed current-season games, as compute_elo expects."""
    fin = games[games.status == 'final'].copy()
    seasons = set(fin.season.astype(int))
    hist = history[~history.season.isin(seasons)]           # never double-count
    cur = pd.DataFrame({
        'date': [et_date(t) for t in fin.tipoff_utc],
        'season': fin.season.astype(int).values,
        'home': fin.home.values, 'away': fin.away.values,
        'home_pts': fin.home_pts.astype(float).values,
        'away_pts': fin.away_pts.astype(float).values,
    })
    cur['home_win'] = (cur.home_pts > cur.away_pts).astype(int)
    return pd.concat([hist, cur], ignore_index=True)


def ratings_as_of(all_games: pd.DataFrame, season: int) -> dict:
    """Elo going into `season`. If that season has no completed games yet, apply
    the off-season regression here (compute_elo only does it on a new season's
    first game) — exactly once either way."""
    _, R = compute_elo(all_games)
    if int(all_games.season.max()) < season:
        R = {t: CARRYOVER * r + (1 - CARRYOVER) * MEAN for t, r in R.items()}
    return R


def rest_flags(all_games: pd.DataFrame, pending: pd.DataFrame) -> pd.DataFrame:
    """Back-to-back flags for pending games, using the latest prior game date
    (completed or also pending) for each team."""
    pend = pending.copy()
    pend['date'] = [et_date(t) for t in pend.tipoff_utc]
    seen = pd.concat([all_games[['date', 'home', 'away']], pend[['date', 'home', 'away']]])
    long = pd.concat([seen[['date', 'home']].rename(columns={'home': 't'}),
                      seen[['date', 'away']].rename(columns={'away': 't'})])
    long['date'] = pd.to_datetime(long['date'])
    by_team = {t: np.sort(g['date'].unique()) for t, g in long.groupby('t')}

    def b2b(team, d):
        ds = by_team.get(team, np.array([], dtype='datetime64[ns]'))
        prior = ds[ds < np.datetime64(d)]
        return int(len(prior) > 0 and (np.datetime64(d) - prior[-1]) == np.timedelta64(1, 'D'))

    pend['home_b2b'] = [b2b(h, d) for h, d in zip(pend.home, pend.date)]
    pend['away_b2b'] = [b2b(a, d) for a, d in zip(pend.away, pend.date)]
    return pend


def predict_rows(pending: pd.DataFrame, R: dict, engine: dict) -> pd.DataFrame:
    out = pending.copy()
    eh = np.array([R.get(t, BASE) for t in out.home])
    ea = np.array([R.get(t, BASE) for t in out.away])
    hca = np.where(out.neutral.astype(int) == 1, 0.0, engine['intercept_hca_points'])
    margin = (engine['b_elo_per_point'] * (eh - ea) + hca
              + engine['home_b2b_points'] * out.home_b2b
              + engine['away_b2b_points'] * out.away_b2b)
    out['margin'] = np.round(margin, 3)
    out['p_home'] = [round(_phi(m / engine['sigma_points']), 4) for m in margin]
    out['elo_home'], out['elo_away'] = np.round(eh, 1), np.round(ea, 1)
    return out


# --------------------------------------------------------------------------- run
def run_update(*, now: datetime, history: pd.DataFrame, fetch, store: Store,
               engine: dict, code_version: str = 'local', run_id: str = 'local') -> dict:
    """One refresh. `fetch(dates) -> raw events` may raise FeedError; on failure
    no data file is written and the last valid state is kept."""
    now = now.astimezone(timezone.utc)
    old_games = store.games()
    # Window, contiguous so no day can be skipped:
    #   from season opening (first run) or the last stored game (later runs,
    #   which also bridges any gap left by missed runs) or RECHECK_DAYS ago,
    #   whichever is earlier, through two days ahead for the upcoming slate.
    today = now.astimezone(ET).date()
    cur_season = season_of(now)
    stored = old_games[old_games.season.astype(int) == cur_season] if len(old_games) else old_games
    if len(stored):
        last_stored = max(parse_ts(t).astimezone(ET).date() for t in stored.tipoff_utc)
        start = min(last_stored, today - timedelta(days=RECHECK_DAYS))
    else:
        start = datetime(cur_season, 10, 1).date()        # backfill from opening
    days = {start + timedelta(days=k) for k in range((today - start).days + 3)}
    if len(old_games):                                   # unresolved older games
        unresolved = old_games[(old_games.status != 'final') &
                               (old_games.tipoff_utc.map(parse_ts) < now)]
        days |= {parse_ts(t).astimezone(ET).date() for t in unresolved.tipoff_utc}
    dates = sorted(days)

    status = store.status()
    status.update({'last_attempt_utc': iso(now), 'run_id': run_id})
    try:
        fresh = normalize(fetch(dates))
    except FeedError as exc:
        status.update({'feed_ok': False, 'last_error': str(exc)})
        store.root.mkdir(parents=True, exist_ok=True)
        store.status_path.write_text(json.dumps(status, indent=2, sort_keys=True))
        return status

    games = merge_games(old_games, fresh)
    all_games = history_with_season(history, games)
    # Games before the first successful run are backfill: they update ratings
    # but are never predicted and never counted as missed.
    tracking_start = parse_ts(status.get('tracking_start_utc') or iso(now))

    preds, missed = store.preds(), store.missed()
    predicted_keys = set(zip(preds.event_id.astype(str), preds.tipoff_utc))
    missed_keys = set(zip(missed.event_id.astype(str), missed.tipoff_utc))

    upcoming = games[games.status == 'scheduled'].copy()
    upcoming['tip'] = upcoming.tipoff_utc.map(parse_ts)
    in_window = upcoming[upcoming.tip <= now + PREDICT_HORIZON]
    new_keys = [k for k in zip(in_window.event_id, in_window.tipoff_utc)
                if k not in predicted_keys]
    todo = in_window.loc[_mask(k in set(new_keys)
                               for k in zip(in_window.event_id, in_window.tipoff_utc))]
    on_time = todo[todo.tip > now + TIPOFF_BUFFER]
    too_late = todo[todo.tip <= now + TIPOFF_BUFFER]

    # Games that started (or finished) with no prediction on record and no
    # missed entry yet: record as missed, never predict after the fact.
    started = games[games.status.isin(['final', 'in_progress'])].copy()
    started = started.loc[_mask(parse_ts(t) <= now for t in started.tipoff_utc)]
    started = started.loc[_mask((e, t) not in predicted_keys and (e, t) not in missed_keys
                                and parse_ts(t) >= tracking_start
                                for e, t in zip(started.event_id, started.tipoff_utc))]
    missed_new = pd.concat([too_late[MISSED_COLS[:4]], started[MISSED_COLS[:4]]])
    missed_new = missed_new.drop_duplicates(['event_id', 'tipoff_utc'])
    missed_new = missed_new.assign(noticed_at_utc=iso(now), run_id=run_id,
                                   reason='no prediction published before tip-off')

    new_preds = pd.DataFrame(columns=PRED_COLS)
    if len(on_time):
        season = int(on_time.season.max())
        R = ratings_as_of(all_games, season)
        flagged = rest_flags(all_games, on_time)
        new_preds = predict_rows(flagged, R, engine).assign(
            predicted_at_utc=iso(now), data_cutoff_utc=iso(now),
            model_version=model_version(engine), code_version=code_version,
            run_id=run_id)[PRED_COLS]

    # Write (append-only for predictions and missed).
    _write(games[GAME_COLS], store.games_path, ['tipoff_utc', 'event_id'])
    _write(_cat(preds, new_preds, PRED_COLS),
           store.preds_path, ['tipoff_utc', 'event_id', 'predicted_at_utc'])
    _write(_cat(missed, missed_new, MISSED_COLS),
           store.missed_path, ['tipoff_utc', 'event_id', 'noticed_at_utc'])

    status.update({
        'tracking_start_utc': iso(tracking_start),
        'feed_ok': True, 'last_error': None,
        'last_success_utc': iso(now),
        'data_cutoff_utc': iso(now),
        'season': int(games.season.max()) if len(games) else None,
        'games_final': int((games.status == 'final').sum()),
        'new_predictions': int(len(new_preds)),
        'new_missed': int(len(missed_new)),
        'model_version': model_version(engine),
    })
    store.status_path.write_text(json.dumps(status, indent=2, sort_keys=True))
    return status


def update_receipts(store: Store, get_run, now: datetime) -> int:
    """Record GitHub's own completion record for each Actions run that produced
    predictions. `get_run(run_id)` returns the /actions/runs/{id} JSON. A run
    cannot vouch for itself (it is still running), so receipts lag one run."""
    preds, rec = store.preds(), store.receipts()
    have = set(rec.run_id.astype(str))
    want = sorted({str(r) for r in preds.run_id.astype(str) if r != 'local'} - have)
    rows = []
    for rid in want:
        try:
            run = get_run(rid)
        except Exception:
            continue                              # try again next time
        if run.get('status') != 'completed':
            continue
        rows.append({'run_id': rid, 'conclusion': run.get('conclusion'),
                     'completed_at_utc': run.get('updated_at'),
                     'head_sha': run.get('head_sha'), 'checked_at_utc': iso(now)})
    if rows:
        _write(_cat(rec, pd.DataFrame(rows), RECEIPT_COLS),
               store.receipts_path, ['run_id'])
    return len(rows)


# --------------------------------------------------------------------------- grade
def eligibility(preds: pd.DataFrame, receipts: pd.DataFrame) -> pd.Series:
    """A prediction is prospectively eligible only if the GitHub Actions run that
    produced it finished successfully (per GitHub's own record) before tip-off,
    at least TIPOFF_BUFFER early. Local runs are never eligible."""
    rec = receipts.set_index(receipts.run_id.astype(str)) if len(receipts) else None

    def ok(row):
        if rec is None or str(row.run_id) == 'local' or str(row.run_id) not in rec.index:
            return False
        r = rec.loc[str(row.run_id)]
        if r.conclusion != 'success':
            return False
        return parse_ts(r.completed_at_utc) <= parse_ts(row.tipoff_utc) - TIPOFF_BUFFER
    return preds.apply(ok, axis=1) if len(preds) else pd.Series(dtype=bool)


def scorecard(store: Store) -> dict:
    games, preds, missed, receipts = store.games(), store.preds(), store.missed(), store.receipts()
    out = {'predictions': int(len(preds)), 'missed': int(len(missed)),
           'eligible': 0, 'graded': 0, 'awaiting_result': 0, 'void_rescheduled': 0,
           'unverified': 0, 'metrics': None, 'reliability': []}
    if not len(preds):
        return out
    p = preds.copy()
    p['eligible'] = eligibility(p, receipts).values
    out['eligible'] = int(p.eligible.sum())
    out['unverified'] = int((~p.eligible).sum())
    g = games.set_index('event_id')
    graded = []
    for row in p[p.eligible].itertuples():
        if row.event_id not in g.index:
            out['awaiting_result'] += 1
            continue
        game = g.loc[row.event_id]
        if abs(parse_ts(game.tipoff_utc) - parse_ts(row.tipoff_utc)) > RESCHEDULE_TOLERANCE:
            out['void_rescheduled'] += 1
            continue
        if game.status != 'final':
            out['awaiting_result'] += 1
            continue
        graded.append((float(row.p_home), int(game.home_pts > game.away_pts)))
    if graded:
        pp = np.clip(np.array([x for x, _ in graded]), 1e-6, 1 - 1e-6)
        y = np.array([v for _, v in graded])
        out['graded'] = len(graded)
        out['metrics'] = {
            'accuracy': round(float(((pp > .5) == (y == 1)).mean()), 4),
            'log_loss': round(float(-(y * np.log(pp) + (1 - y) * np.log(1 - pp)).mean()), 4),
            'brier': round(float(((pp - y) ** 2).mean()), 4)}
        edges = np.linspace(0, 1, 6)
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (pp >= lo) & (pp < hi if hi < 1 else pp <= hi)
            if m.sum():
                out['reliability'].append({'predicted': round(float(pp[m].mean()), 3),
                                           'observed': round(float(y[m].mean()), 3),
                                           'n': int(m.sum())})
    return out
