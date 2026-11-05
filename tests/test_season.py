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


def run(env, now=NOW, run_id='local', run_attempt='1'):
    return S.run_update(now=now, history=env['history'], fetch=env['feed'],
                        store=env['store'], engine=env['engine'], run_id=run_id,
                        run_attempt=run_attempt)


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
    _receipt_all(env['store'])
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
def _receipt_all(store, completed=None, conclusion='success', lag=timedelta(minutes=2)):
    """Write a receipt for every (run_id, run_attempt) in the ledger. With no
    `completed`, each attempt finishes `lag` after its own predictions."""
    preds = store.preds()
    rows = []
    for (r, a), grp in preds.groupby([preds.run_id.astype(str), preds.run_attempt.astype(str)]):
        done = completed or S.iso(max(S.parse_ts(t) for t in grp.predicted_at_utc) + lag)
        rows.append({'run_id': r, 'run_attempt': a, 'conclusion': conclusion,
                     'completed_at_utc': done, 'head_sha': 'x', 'checked_at_utc': done})
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

    def get_attempt(rid, att):
        calls.append((rid, att))
        return {'id': int(rid), 'run_attempt': int(att), 'status': 'completed',
                'conclusion': 'success', 'updated_at': '2026-11-04T18:03:00Z',
                'head_sha': 'abc'}
    n = S.update_receipts(env['store'], get_attempt, NOW)
    assert n == 1 and calls == [('222', '1')]
    assert S.update_receipts(env['store'], get_attempt, NOW) == 0   # not re-fetched


def test_scorecard_grades_finished_games(env):
    run(env, run_id='333')
    env['feed'].set(3, status='STATUS_FINAL', home_score='112', away_score='100')
    env['feed'].set(4, status='STATUS_FINAL', home_score='101', away_score='108')
    run(env, now=datetime(2026, 11, 5, 15, 0, tzinfo=UTC), run_id='334')
    _receipt_all(env['store'], completed='2026-11-04T18:05:00Z')
    sc = S.scorecard(env['store'])
    assert sc['graded'] == 2 and sc['metrics']['log_loss'] > 0
    assert sc['missed'] == 0


# ------------------------------------------------------------------ review regressions
def test_small_tipoff_change_keeps_original_prediction(env):
    """[P1] A 30-minute tip-off change is the same game: no second prediction,
    and the event is graded once."""
    run(env, run_id='601')
    p3 = env['store'].preds().query("event_id == '3'").iloc[0]
    env['feed'].set(3, date='2026-11-05T01:00Z')             # 7:30pm -> 8:00pm ET
    st = run(env, now=NOW + timedelta(hours=2), run_id='602')
    rows = env['store'].preds().query("event_id == '3'")
    assert len(rows) == 1 and st['new_predictions'] == 0
    assert rows.iloc[0].p_home == p3.p_home
    env['feed'].set(3, status='STATUS_FINAL', home_score='110', away_score='100')
    run(env, now=datetime(2026, 11, 5, 12, 0, tzinfo=UTC), run_id='603')
    _receipt_all(env['store'])
    sc = S.scorecard(env['store'])
    assert sc['void_rescheduled'] == 0
    assert sc['graded'] == 1                                 # event 3 counted once


def test_genuine_reschedule_supersedes_and_scores_once(env):
    """[P1] Beyond tolerance a new prediction is made, explicitly superseding the
    old one; at most one prediction per event is ever scored."""
    run(env, run_id='611')
    old_id = env['store'].preds().query("event_id == '3'").iloc[0].prediction_id
    env['feed'].set(3, date='2026-11-06T00:30Z')             # moved a full day
    run(env, now=datetime(2026, 11, 5, 18, 0, tzinfo=UTC), run_id='612')
    rows = env['store'].preds().query("event_id == '3'").sort_values('predicted_at_utc')
    assert len(rows) == 2 and rows.iloc[1].supersedes == old_id
    assert rows.iloc[0].supersedes == ''
    env['feed'].set(3, status='STATUS_FINAL', home_score='100', away_score='90')
    run(env, now=datetime(2026, 11, 6, 12, 0, tzinfo=UTC), run_id='613')
    _receipt_all(env['store'])
    sc = S.scorecard(env['store'])
    assert sc['void_rescheduled'] == 1 and sc['graded'] == 1


def test_receipts_are_per_attempt(env):
    """[P2->P1] A re-run reuses the run ID. Attempt 1's prediction must be judged
    by attempt 1's completion, and a later attempt cannot vouch for it."""
    run(env, run_id='700', run_attempt='1')
    store = env['store']
    seen = []

    def get_attempt(rid, att):
        seen.append((rid, att))
        # attempt 1 failed; a hypothetical attempt 2 succeeded early
        ok = att == '2'
        return {'id': int(rid), 'run_attempt': int(att), 'status': 'completed',
                'conclusion': 'success' if ok else 'failure',
                'updated_at': '2026-11-04T18:04:00Z', 'head_sha': 'abc'}
    S.update_receipts(store, get_attempt, NOW)
    assert seen == [('700', '1')]                            # asked for the exact attempt
    assert S.scorecard(store)['eligible'] == 0               # attempt 1 failed

    # A mismatched attempt record is never accepted.
    run(env, now=NOW + timedelta(minutes=30), run_id='701', run_attempt='3')
    env['feed'].events.append(ev(11, '2026-11-05T01:30Z', 'NY', 'LAL'))
    run(env, now=NOW + timedelta(minutes=40), run_id='701', run_attempt='3')
    wrong = lambda rid, att: {'id': int(rid), 'run_attempt': 1, 'status': 'completed',
                              'conclusion': 'success', 'updated_at': '2026-11-04T19:00:00Z',
                              'head_sha': 'abc'}
    S.update_receipts(store, wrong, NOW)
    assert ('701', '3') not in set(zip(store.receipts().run_id.astype(str),
                                       store.receipts().run_attempt.astype(str)))


def test_completion_before_prediction_is_not_eligible(env):
    """predicted_at <= completion <= tipoff - buffer, both bounds enforced."""
    run(env, run_id='710')
    _receipt_all(env['store'], completed='2026-11-04T17:59:00Z')  # before predicted_at
    assert S.scorecard(env['store'])['eligible'] == 0
    _receipt_all(env['store'], completed='2026-11-04T18:00:00Z')  # equal is fine
    assert S.scorecard(env['store'])['eligible'] == 2


def test_missed_game_logged_once_across_runs(env):
    """[P2] Repeated runs inside the buffer, and after tip-off, add one missed row."""
    run(env)
    env['feed'].events.append(ev(12, '2026-11-05T03:05Z', 'PHI', 'LAL'))
    run(env, now=datetime(2026, 11, 5, 2, 58, tzinfo=UTC))       # inside buffer
    run(env, now=datetime(2026, 11, 5, 3, 0, tzinfo=UTC))        # inside buffer again
    env['feed'].set(12, status='STATUS_IN_PROGRESS')
    run(env, now=datetime(2026, 11, 5, 3, 30, tzinfo=UTC))       # now underway
    env['feed'].set(12, status='STATUS_FINAL', home_score='100', away_score='99')
    run(env, now=datetime(2026, 11, 5, 6, 0, tzinfo=UTC))
    m = env['store'].missed()
    assert (m.event_id == '12').sum() == 1
    assert S.scorecard(env['store'])['missed'] == 1


def test_back_to_back_counts_game_in_progress(env):
    """[P2] A team playing right now is on a back-to-back tomorrow, even though
    the unfinished game must not touch Elo."""
    run(env)
    env['feed'].set(4, status='STATUS_IN_PROGRESS')          # DEN v LAL underway
    env['feed'].events.append(ev(13, '2026-11-06T00:00Z', 'LAL', 'NY'))  # LAL next night
    now = datetime(2026, 11, 5, 2, 30, tzinfo=UTC)
    run(env, now=now)
    p = env['store'].preds().set_index('event_id')
    assert int(p.loc['13', 'home_b2b']) == 1 and int(p.loc['13', 'away_b2b']) == 0
    g = env['store'].games()
    R_with = S.ratings_as_of(S.history_with_season(env['history'], g), 2026)
    R_finals = S.ratings_as_of(S.history_with_season(
        env['history'], g[g.status == 'final']), 2026)
    assert R_with == R_finals                                # in-progress game ignored by Elo
