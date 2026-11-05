"""Tests for src/season.py.

Covers the five scenarios required before the live-season tracker is accepted
(duplicate run, late run, postponed game, corrected final, feed failure) plus
the backfill, neutral-site, regression, validation and eligibility rules.

Run:  python -m pytest tests/ -q
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import season as S  # noqa: E402

UTC = timezone.utc
NOW = datetime(2026, 11, 4, 18, 0, tzinfo=UTC)          # 1pm ET, before tonight's games
TEAMS6 = ['BOS', 'NYK', 'PHI', 'MIA', 'LAL', 'DEN']


# ------------------------------------------------------------------ fixtures
def make_history() -> pd.DataFrame:
    """Two small past seasons so Elo has something to carry over."""
    rows, rng = [], np.random.default_rng(0)
    d = pd.Timestamp('2024-10-25')
    for season in (2024, 2025):
        d = pd.Timestamp(f'{season}-10-25')
        for i in range(60):
            h, a = rng.choice(TEAMS6, 2, replace=False)
            hp = int(rng.integers(95, 130)); ap = int(rng.integers(95, 130))
            ap = ap + 1 if ap == hp else ap
            rows.append({'date': d + pd.Timedelta(days=i), 'season': season, 'home': h,
                         'away': a, 'home_pts': float(hp), 'away_pts': float(ap),
                         'home_win': int(hp > ap)})
    return pd.DataFrame(rows)


def ev(eid, tip, home, away, status='STATUS_SCHEDULED', hs=None, as_=None, neutral=False):
    return {'id': str(eid), 'date': tip, 'status': status, 'home': home, 'away': away,
            'home_score': hs, 'away_score': as_, 'neutral': neutral}


def base_feed():
    """Season so far: two finals last week, one tonight's game, one far future."""
    return [
        ev(1, '2026-10-28T23:30Z', 'BOS', 'NY', 'STATUS_FINAL', '110', '101'),
        ev(2, '2026-10-29T00:00Z', 'MIA', 'PHI', 'STATUS_FINAL', '99', '104'),
        ev(3, '2026-11-05T00:30Z', 'BOS', 'MIA'),              # tonight
        ev(4, '2026-11-05T02:00Z', 'DEN', 'LAL'),              # tonight, later
        ev(5, '2026-11-09T00:00Z', 'NY', 'PHI'),               # beyond horizon
    ]


class Feed:
    """Fake scoreboard: returns whatever events are set, records calls."""
    def __init__(self, events):
        self.events, self.calls, self.fail = list(events), 0, None

    def __call__(self, dates):
        self.calls += 1
        if self.fail:
            raise S.FeedError(self.fail)
        ds = {str(d) for d in dates}
        return [e for e in self.events
                if str(S.parse_ts(e['date']).astimezone(S.ET).date()) in ds]

    def set(self, eid, **kw):
        for e in self.events:
            if e['id'] == str(eid):
                e.update(kw)


@pytest.fixture
def env(tmp_path):
    return {'store': S.Store(root=tmp_path / 'season'), 'history': make_history(),
            'engine': S.load_engine(), 'feed': Feed(base_feed())}


def run(env, now=NOW, run_id='local'):
    return S.run_update(now=now, history=env['history'], fetch=env['feed'],
                        store=env['store'], engine=env['engine'], run_id=run_id)


def snapshot(store):
    return {p.name: p.read_bytes() for p in
            [store.games_path, store.preds_path, store.missed_path] if p.exists()}


# ------------------------------------------------------------------ 1. duplicate run
def test_duplicate_run_is_idempotent(env):
    run(env)
    first = snapshot(env['store'])
    st = run(env)
    assert snapshot(env['store']) == first, 'second identical run changed data files'
    assert st['new_predictions'] == 0 and st['new_missed'] == 0
    assert len(env['store'].preds()) == 2                 # events 3 and 4 only


# ------------------------------------------------------------------ 2. late run
def test_late_run_records_missed_not_predictions(env):
    run(env)                                                 # establishes tracking start
    # A brand-new game is added that has already tipped off by the next run.
    env['feed'].events.append(ev(6, '2026-11-05T01:00Z', 'NY', 'DEN', 'STATUS_IN_PROGRESS'))
    late = datetime(2026, 11, 5, 1, 30, tzinfo=UTC)
    st = run(env, now=late)
    preds, missed = env['store'].preds(), env['store'].missed()
    assert '6' not in set(preds.event_id), 'predicted a game after tip-off'
    assert '6' in set(missed.event_id)
    assert st['new_predictions'] == 0


def test_inside_buffer_counts_as_missed(env):
    run(env)
    env['feed'].events.append(ev(7, '2026-11-05T03:05Z', 'PHI', 'LAL'))
    st = run(env, now=datetime(2026, 11, 5, 3, 0, tzinfo=UTC))   # 5 min before tip
    assert '7' in set(env['store'].missed().event_id)
    assert '7' not in set(env['store'].preds().event_id)


def test_backfill_is_never_counted_as_missed(env):
    st = run(env)                                            # first ever run
    assert st['games_final'] == 2
    assert len(env['store'].missed()) == 0, 'pre-tracking finals marked as missed'


# ------------------------------------------------------------------ 3. postponed game
def test_postponed_then_rescheduled_voids_old_prediction(env):
    run(env, run_id='501')
    original = env['store'].preds()
    p3 = original[original.event_id == '3'].iloc[0].to_dict()

    env['feed'].set(3, status='STATUS_POSTPONED')
    run(env, now=datetime(2026, 11, 4, 23, 0, tzinfo=UTC), run_id='502')
    assert '3' not in set(env['store'].missed().event_id), 'postponed game marked missed'
    env['feed'].set(3, status='STATUS_SCHEDULED', date='2026-11-08T00:30Z')
    run(env, now=datetime(2026, 11, 7, 18, 0, tzinfo=UTC), run_id='503')

    preds = env['store'].preds()
    rows = preds[preds.event_id == '3']
    assert len(rows) == 2, 'expected a fresh prediction for the new tip-off'
    kept = rows[rows.tipoff_utc == p3['tipoff_utc']].iloc[0]
    assert kept.p_home == p3['p_home'] and kept.predicted_at_utc == p3['predicted_at_utc'], \
        'original prediction was rewritten'

    env['feed'].set(3, status='STATUS_FINAL', home_score='105', away_score='100')
    run(env, now=datetime(2026, 11, 8, 12, 0, tzinfo=UTC), run_id='504')
    # Treat the runs as verified so grading logic is exercised.
    _receipt_all(env['store'], completed='2026-11-01T00:00:00Z')
    sc = S.scorecard(env['store'])
    assert sc['void_rescheduled'] == 1                       # old tip-off, voided
    assert sc['graded'] >= 1                                 # new tip-off, graded


# ------------------------------------------------------------------ 4. corrected final
def test_corrected_final_updates_ratings_not_predictions(env):
    run(env)
    preds_before = env['store'].preds().copy()
    g = env['store'].games()
    R1 = S.ratings_as_of(S.history_with_season(env['history'], g), 2026)

    env['feed'].set(1, home_score='90', away_score='120')   # stat correction flips result
    run(env, now=NOW + timedelta(hours=1))
    g2 = env['store'].games()
    row = g2[g2.event_id == '1'].iloc[0]
    assert (row.home_pts, row.away_pts) == (90, 120)
    R2 = S.ratings_as_of(S.history_with_season(env['history'], g2), 2026)
    assert R2['BOS'] < R1['BOS'] and R2['NYK'] > R1['NYK']
    pd.testing.assert_frame_equal(env['store'].preds(), preds_before)


# ------------------------------------------------------------------ 5. feed failure
def test_feed_failure_preserves_last_valid_data(env):
    run(env)
    before = snapshot(env['store'])
    env['feed'].fail = 'HTTPError 503'
    st = run(env, now=NOW + timedelta(hours=3))
    assert snapshot(env['store']) == before
    assert st['feed_ok'] is False and '503' in st['last_error']
    assert st['last_success_utc'] == S.iso(NOW)             # still the last good run


def test_bad_data_is_rejected_whole(env):
    run(env)
    before = snapshot(env['store'])
    env['feed'].set(2, home_score='104', away_score='104')   # a tie can't happen
    st = run(env, now=NOW + timedelta(hours=1))
    assert st['feed_ok'] is False and snapshot(env['store']) == before

    env['feed'].set(2, home_score='99')                      # repair, then unknown team
    env['feed'].events.append(ev(9, '2026-11-05T01:00Z', 'SEA', 'BOS'))
    st = run(env, now=NOW + timedelta(hours=2))
    assert st['feed_ok'] is False and snapshot(env['store']) == before


# ------------------------------------------------------------------ model rules
def test_neutral_site_gets_no_home_court(env):
    env['feed'].events.append(ev(8, '2026-11-05T01:00Z', 'NY', 'PHI', neutral=True))
    env['feed'].events.append(ev(10, '2026-11-05T01:00Z', 'LAL', 'MIA'))
    run(env)
    p = env['store'].preds().set_index('event_id')
    R = S.ratings_as_of(S.history_with_season(env['history'], env['store'].games()), 2026)
    eng = env['engine']
    neutral_margin = eng['b_elo_per_point'] * (R['NYK'] - R['PHI'])
    assert p.loc['8', 'margin'] == pytest.approx(neutral_margin, abs=1e-3)
    home_margin = eng['b_elo_per_point'] * (R['LAL'] - R['MIA']) + eng['intercept_hca_points']
    assert p.loc['10', 'margin'] == pytest.approx(home_margin, abs=1e-3)


def test_offseason_regression_applied_exactly_once(env):
    hist = env['history']
    _, end_2025 = S.compute_elo(hist)
    before_any_game = S.ratings_as_of(hist, 2026)            # no 2026 games yet
    for t, r in end_2025.items():
        assert before_any_game[t] == pytest.approx(S.CARRYOVER * r + (1 - S.CARRYOVER) * S.MEAN)
    # Replaying twice gives identical ratings (no compounding).
    assert S.ratings_as_of(hist, 2026) == before_any_game


def test_horizon_and_season_labels(env):
    run(env)
    p = env['store'].preds()
    assert set(p.event_id) == {'3', '4'}                     # event 5 is 4+ days out
    assert set(env['store'].games().season) == {2026}


def test_espn_abbreviations_are_mapped(env):
    run(env)
    teams = set(env['store'].games()[['home', 'away']].values.ravel())
    assert teams <= S.TEAMS and 'NYK' in teams and 'NY' not in teams


# ------------------------------------------------------------------ eligibility
def _receipt_all(store, completed, conclusion='success'):
    preds = store.preds()
    rows = [{'run_id': r, 'conclusion': conclusion, 'completed_at_utc': completed,
             'head_sha': 'x', 'checked_at_utc': completed}
            for r in sorted(set(preds.run_id.astype(str)))]
    pd.DataFrame(rows, columns=S.RECEIPT_COLS).to_csv(store.receipts_path, index=False)


def test_local_predictions_are_never_eligible(env):
    run(env)                                                 # run_id = 'local'
    _receipt_all(env['store'], completed='2026-11-04T18:01:00Z')
    sc = S.scorecard(env['store'])
    assert sc['eligible'] == 0 and sc['unverified'] == 2


def test_eligibility_requires_publication_before_tipoff(env):
    run(env, run_id='111')
    store = env['store']
    _receipt_all(store, completed='2026-11-04T18:02:00Z')   # finished well before tips
    assert S.scorecard(store)['eligible'] == 2
    _receipt_all(store, completed='2026-11-05T00:25:00Z')   # inside buffer of 00:30 game
    sc = S.scorecard(store)
    assert sc['eligible'] == 1                               # only the 02:00 game
    _receipt_all(store, completed='2026-11-04T18:02:00Z', conclusion='failure')
    assert S.scorecard(store)['eligible'] == 0


def test_receipts_come_from_github_record(env):
    run(env, run_id='222')
    calls = []

    def get_run(rid):
        calls.append(rid)
        return {'status': 'completed', 'conclusion': 'success',
                'updated_at': '2026-11-04T18:03:00Z', 'head_sha': 'abc'}
    n = S.update_receipts(env['store'], get_run, NOW)
    assert n == 1 and calls == ['222']
    assert S.update_receipts(env['store'], get_run, NOW) == 0   # not re-fetched


def test_scorecard_grades_finished_games(env):
    run(env, run_id='333')
    env['feed'].set(3, status='STATUS_FINAL', home_score='112', away_score='100')
    env['feed'].set(4, status='STATUS_FINAL', home_score='101', away_score='108')
    run(env, now=datetime(2026, 11, 5, 15, 0, tzinfo=UTC), run_id='334')
    _receipt_all(env['store'], completed='2026-11-04T18:05:00Z')
    sc = S.scorecard(env['store'])
    assert sc['graded'] == 2 and sc['metrics']['log_loss'] > 0
    assert sc['missed'] == 0
