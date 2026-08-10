"""Live NBA injury report (Tier 3).

Pulls the current injury list from ESPN's public feed (free, no key), maps each
listed player to a team, and normalises the status. The app uses it to auto-sit
players who are Out/Doubtful and to badge everyone else's status. Works on the
user's machine; if the feed is unreachable the app just falls back to manual
toggles.

Status buckets:
  out       -> Out / Doubtful            (sit by default)
  gtd       -> Questionable / Day-To-Day (play, but flagged)
  probable  -> Probable / Available      (play)
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / 'data' / 'live'
ESPN = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries'

SIT_STATUSES = {'out', 'doubtful'}
GTD_STATUSES = {'questionable', 'day-to-day', 'day to day', 'game-time decision'}


def norm_name(n: str) -> str:
    """Lowercase, strip accents/punctuation and Jr/Sr/III suffixes for matching."""
    n = unicodedata.normalize('NFKD', n or '').encode('ascii', 'ignore').decode()
    n = n.lower().replace('.', '').replace("'", '')
    n = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '', n)
    return re.sub(r'\s+', ' ', n).strip()


def bucket(status: str) -> str:
    s = (status or '').lower().strip()
    if s in SIT_STATUSES:
        return 'out'
    if s in GTD_STATUSES:
        return 'gtd'
    return 'probable'


def fetch_injuries() -> dict:
    """Fetch and cache the current injury report. Returns the parsed dict."""
    import requests
    r = requests.get(ESPN, timeout=15,
                     headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    r.raise_for_status()
    data = r.json()

    items = []
    for grp in data.get('injuries', []):
        team = grp.get('displayName') or (grp.get('team') or {}).get('displayName', '')
        for inj in grp.get('injuries', []):
            ath = inj.get('athlete') or {}
            player = ath.get('displayName') or ath.get('fullName')
            if not player:
                continue
            status = (inj.get('status') or (inj.get('type') or {}).get('description') or '')
            det = inj.get('details') or {}
            detail = ' '.join(x for x in [det.get('type'), det.get('detail')] if x) \
                or inj.get('shortComment', '') or ''
            items.append({'team': team, 'player': player, 'status': status,
                          'bucket': bucket(status), 'detail': detail[:80]})

    out = {'fetched': datetime.now().isoformat(timespec='seconds'),
           'count': len(items), 'items': items}
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / 'injuries.json').write_text(json.dumps(out, indent=2))
    return out


def load_injuries() -> dict | None:
    p = LIVE / 'injuries.json'
    return json.loads(p.read_text()) if p.exists() else None


def by_team(report: dict, name_to_abbr: dict) -> dict:
    """-> {abbr: {norm_name: {'status','bucket','detail','player'}}}."""
    result: dict = {}
    for it in (report or {}).get('items', []):
        abbr = name_to_abbr.get(it['team'])
        if not abbr:
            continue
        result.setdefault(abbr, {})[norm_name(it['player'])] = it
    return result
