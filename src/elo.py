"""538-style Elo power ratings for NBA teams.

Ratings are *neutral* team strength (no home court baked into the number);
home-court advantage is applied only at prediction time, the way
FiveThirtyEight does it. Uses a margin-of-victory multiplier with the
autocorrelation correction so blowouts help but don't runaway-inflate the
best teams, plus season-to-season mean reversion.

Refs:
  538 K-factor / MOV: K = 20*(MOV+3)^0.8 / (7.5 + 0.006*ΔElo_winner)
  https://andr3w321.com/elo-ratings-part-2-margin-of-victory-adjustments/
"""
from __future__ import annotations

import numpy as np
import pandas as pd

BASE = 1500.0
MEAN = 1505.0            # long-run league mean ratings revert toward
CARRYOVER = 0.75        # keep 75% of last season's rating, revert 25% to MEAN
HCA_ELO = 70.0          # home bonus used only inside the win-expectation
K0 = 20.0


def _expected(r_home_adj: float, r_away: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r_away - r_home_adj) / 400.0))


def compute_elo(games: pd.DataFrame, hca_elo: float = HCA_ELO,
                carryover: float = CARRYOVER) -> tuple[pd.DataFrame, dict]:
    """Add pre-game neutral Elo columns to `games` and return final ratings.

    games needs: date, season, home, away, home_pts, away_pts, home_win
    Returns (games_with_elo, final_ratings_dict).
    """
    g = games.sort_values('date').reset_index(drop=True).copy()
    R: dict[str, float] = {}
    last_season: dict[str, int] = {}
    cur_season_seen = None

    eh = np.full(len(g), np.nan)
    ea = np.full(len(g), np.nan)

    for i, row in enumerate(g.itertuples()):
        h, a, season = row.home, row.away, row.season
        # season rollover: revert every team once when a new season starts
        if season != cur_season_seen:
            cur_season_seen = season
            for t in list(R):
                R[t] = carryover * R[t] + (1 - carryover) * MEAN
        rh, ra = R.get(h, BASE), R.get(a, BASE)
        eh[i], ea[i] = rh, ra                      # neutral pre-game ratings

        rh_adj = rh + hca_elo
        e_home = _expected(rh_adj, ra)
        s_home = float(row.home_win)
        margin = abs(row.home_pts - row.away_pts)

        # winner-minus-loser elo gap (home-adjusted) for autocorrelation term
        elo_gap_w = (rh_adj - ra) if s_home == 1 else (ra - rh_adj)
        k = K0 * ((margin + 3) ** 0.8) / (7.5 + 0.006 * elo_gap_w)
        delta = k * (s_home - e_home)
        R[h] = rh + delta
        R[a] = ra - delta

    g['elo_home_pre'] = eh
    g['elo_away_pre'] = ea
    g['elo_diff_pre'] = eh - ea
    return g, dict(sorted(R.items(), key=lambda kv: -kv[1]))


def win_prob_from_elo(elo_diff: float, hca_elo: float = HCA_ELO,
                      home_court: bool = True) -> float:
    """Baseline Elo win probability (used as an evaluation benchmark)."""
    adj = elo_diff + (hca_elo if home_court else 0.0)
    return 1.0 / (1.0 + 10 ** (-adj / 400.0))
