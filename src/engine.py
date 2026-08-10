"""Point-spread prediction engine (Tier 1 backbone).

Everything is denominated in POINTS and added up, then converted once to a
win probability with the normal CDF (sigma ~ 12.5). This makes home court,
rest, and player availability principled, additive, and independently checkable.

    margin = b_elo*(elo_home - elo_away)      # neutral power-rating gap
             + HCA                             # +2.47 if home court ON, else 0
             + rest terms                      # B2B penalties
             + player_points                   # from availability toggles
    P(home win) = Phi(margin / sigma)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


class SpreadEngine:
    def __init__(self, path: Path | str | None = None):
        path = Path(path) if path else ROOT / 'models' / 'engine.json'
        self.p = json.loads(Path(path).read_text())
        self.elo = self.p['final_elo']
        self.hca = self.p['intercept_hca_points']
        self.b_elo = self.p['b_elo_per_point']
        self.home_b2b = self.p['home_b2b_points']
        self.away_b2b = self.p['away_b2b_points']
        self.sigma = self.p['sigma_points']
        self.net_rating = self.p.get('season_net_rating', {})

        # 2026-27 projection (current rosters). If present, it drives power.
        proj = ROOT / 'models' / 'projection_2027.json'
        if proj.exists():
            self.power = json.loads(proj.read_text())['power']
            self.projected = True
            self.season_label = '2026-27 (projected)'
        else:
            self.power = {t: self.b_elo * (self.elo[t] - 1500) for t in self.elo}
            self.projected = False
            self.season_label = '2025-26'

    def teams(self):
        return sorted(self.power)

    def team_strength(self, team: str) -> float:
        """Team power in points vs a league-average team."""
        return self.power.get(team, 0.0)

    def power_margin(self, home: str, away: str) -> float:
        """Neutral-court expected margin from power ratings only (no HCA/rest)."""
        return self.power[home] - self.power[away]

    def predict(self, home: str, away: str, *, home_court: bool = True,
                home_rest: int = 2, away_rest: int = 2,
                player_points: float = 0.0, travel_points: float = 0.0) -> dict:
        base = self.power_margin(home, away)
        hca = self.hca if home_court else 0.0
        rest = 0.0
        if int(home_rest) == 1:
            rest += self.home_b2b        # home tired -> negative
        if int(away_rest) == 1:
            rest += self.away_b2b        # away tired -> positive for home
        travel = travel_points if home_court else 0.0   # neutral court = no travel edge
        margin = base + hca + rest + player_points + travel
        prob = _phi(margin / self.sigma)
        rest_pl_tr = rest + player_points + travel
        return {
            'prob_home': prob,
            'margin': margin,
            'components': {
                'power': base,
                'home_court': hca,
                'rest': rest,
                'players': player_points,
                'travel': travel,
            },
            'prob_neutral': _phi((base + rest + player_points) / self.sigma),
            'prob_with_hca': _phi((base + self.hca + rest_pl_tr) / self.sigma),
            'spread_str': _spread_str(margin, home, away),
        }


def _spread_str(margin: float, home: str, away: str) -> str:
    fav, dog, m = (home, away, margin) if margin >= 0 else (away, home, -margin)
    return f'{fav} -{m:.1f}' if m >= 0.05 else 'pick’em'
