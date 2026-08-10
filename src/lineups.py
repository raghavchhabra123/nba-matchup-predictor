"""Minutes-redistribution lineup model (Tier 2).

Team on-court value ≈ Σ BPM_i × (minutes_i / 48), since a lineup's net rating
≈ the sum of its five players' BPM, and integrating over a game divides the
240 player-minutes by 48. When a player sits, his minutes flow to the rest of
the rotation (capped), and any overflow to a replacement-level player
(BPM = -2.0). This makes DEPTH matter: a team with a strong bench barely
notices a star resting; a shallow team craters.

The engine only needs the *change* vs full strength (Elo already encodes the
healthy team), so player_points = Δhome − Δaway.
"""
from __future__ import annotations

import pandas as pd

REPLACEMENT_BPM = -2.0
MAX_MIN = 40.0          # nobody realistically plays more than ~40 mpg
GAME_MIN = 240.0        # 5 players × 48 minutes
ROTATION = 10           # model the top-10 by minutes
CALIBRATION = 0.72      # scales raw BPM-swing to match market injury moves (~5 pts/star)


def _fill_minutes(base: dict[str, float], sitting: set[str]) -> tuple[dict, float]:
    """Distribute GAME_MIN across available players (cap MAX_MIN); return
    (assigned_minutes, replacement_minutes)."""
    avail = {p: m for p, m in base.items() if p not in sitting}
    if not avail:
        return {}, GAME_MIN
    assigned = dict(avail)
    total = sum(assigned.values())
    remaining = GAME_MIN - total
    # add freed minutes proportionally, respecting the per-player cap
    for _ in range(20):
        if remaining <= 1e-6:
            break
        room = {p: MAX_MIN - assigned[p] for p in assigned if assigned[p] < MAX_MIN}
        if not room:
            break
        room_total = sum(room.values())
        give = min(remaining, room_total)
        for p, r in room.items():
            assigned[p] += give * (r / room_total)
        remaining -= give
    replacement = max(0.0, remaining)   # couldn't fit -> replacement-level player
    return assigned, replacement


def _value(assigned: dict[str, float], bpm: dict[str, float],
           replacement_min: float) -> float:
    v = sum(bpm[p] * m / 48.0 for p, m in assigned.items())
    v += REPLACEMENT_BPM * replacement_min / 48.0
    return v


def team_delta(roster: pd.DataFrame, sitting_names: list[str]) -> float:
    """Change in a team's expected margin (pts) when `sitting_names` sit out.

    roster: rows with athlete_display_name, bpm, min_pg (one team).
    """
    rot = roster.sort_values('min_pg', ascending=False).head(ROTATION)
    if rot.empty:
        return 0.0
    # renormalize base minutes so the healthy rotation totals a full game
    scale = GAME_MIN / rot.min_pg.sum()
    base = {r.athlete_display_name: r.min_pg * scale for r in rot.itertuples()}
    bpm = {r.athlete_display_name: r.bpm for r in rot.itertuples()}
    sitting = {n for n in sitting_names if n in base}

    full_assigned, full_repl = _fill_minutes(base, set())
    dep_assigned, dep_repl = _fill_minutes(base, sitting)
    delta = _value(dep_assigned, bpm, dep_repl) - _value(full_assigned, bpm, full_repl)
    return delta * CALIBRATION


def home_player_points(home_roster, away_roster,
                       home_out: list[str], away_out: list[str]) -> float:
    """Net shift to the HOME expected margin from both teams' absences."""
    return team_delta(home_roster, home_out) - team_delta(away_roster, away_out)
