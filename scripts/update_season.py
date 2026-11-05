"""Refresh the current-season tracker.

Fetches ESPN scoreboard results, rebuilds ratings, logs pre-tip-off
predictions, records missed games, and collects GitHub's completion record
for earlier Actions runs (used to prove predictions were published before
tip-off). See src/season.py for the rules.

Run:  python -m scripts.update_season
Exit code 1 if the feed failed (status.json still records the failure and the
last valid data is kept), so a failed refresh is visible in the Actions UI.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import season as S  # noqa: E402


def code_version() -> str:
    sha = os.environ.get('GITHUB_SHA')
    if sha:
        return sha[:12]
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short=12', 'HEAD'],
                                       cwd=ROOT, text=True).strip()
    except Exception:
        return 'unknown'


def github_run_getter():
    """Return get_run(run_id) for this repository, or None outside Actions."""
    repo, token = os.environ.get('GITHUB_REPOSITORY'), os.environ.get('GITHUB_TOKEN')
    if not repo:
        return None
    import requests
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    def get_run(run_id):
        r = requests.get(f'https://api.github.com/repos/{repo}/actions/runs/{run_id}',
                         headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()
    return get_run


def main() -> int:
    now = datetime.now(timezone.utc)
    store = S.Store()
    run_id = os.environ.get('GITHUB_RUN_ID', 'local')
    history = pd.read_csv(ROOT / 'data' / 'games_history.csv', parse_dates=['date'])

    get_run = github_run_getter()
    if get_run:
        n = S.update_receipts(store, get_run, now)
        print(f'receipts: {n} earlier run(s) verified')

    status = S.run_update(now=now, history=history, fetch=S.fetch_events, store=store,
                          engine=S.load_engine(), code_version=code_version(),
                          run_id=run_id)
    print(json.dumps(status, indent=2, sort_keys=True))
    sc = S.scorecard(store)
    print(f"scorecard: {sc['graded']} graded, {sc['eligible']} eligible, "
          f"{sc['missed']} missed, metrics={sc['metrics']}")
    return 0 if status.get('feed_ok') else 1


if __name__ == '__main__':
    sys.exit(main())
