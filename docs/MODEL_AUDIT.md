# Model Audit — what the model accounts for, and what it doesn't

An honest inventory of the factors that move NBA games, whether the model
captures them, and whether the gaps are worth closing.

## ✅ Covered well
| Factor | How | Size |
|---|---|---|
| Team strength (opponent-adjusted) | Elo + 2026-27 roster projection | dominant |
| Home court | refit on recent seasons | **+2.0 pts** |
| Back-to-back rest | fitted B2B term per side | ~2 pts |
| Travel distance + eastward jet lag | haversine + timezone term | up to ~1.5 |
| Altitude (Denver/Utah) | explicit bonus | +1.2 to +2.2 |
| Player availability / injuries | BPM + minutes-redistribution (depth) | 3–7 for a star |
| Offseason roster turnover | players reassigned to current teams | large |

## ⚠️ Real gaps (worth considering, in priority order)
1. **Cumulative fatigue** — 3-games-in-4-nights, 4-in-5, long road trips. Research
   puts this at **1–3 pts** beyond a single back-to-back. We only model one B2B.
   Blocker: needs a real schedule (2026-27 isn't out), so today it could only be a
   manual input. ([schedule-density study](https://www.researchgate.net/publication/357856729_Hiding_in_plain_sight_schedule_density_and_travel_influence_on_NBA_game_outcomes))
2. **Aging** — the roster projection reuses last season's BPM with no age curve.
   Players peak ~27 and decline after ~30-31; young cores improve. Worth ~1–2 pts
   for old/young teams over a season. Blocker: we don't store player ages yet.
3. **3-point variance → confidence** — 3PT-heavy teams are more volatile
   game-to-game. This shouldn't change *who's* favored but should **widen the
   win-probability band** (bigger sigma) so extreme %s are less overconfident.
   A calibration/uncertainty refinement, not a mean shift.
   ([variance research](https://arxiv.org/pdf/2606.27957))
4. **Roster continuity / chemistry** — teams with heavy turnover start slow.
   Partly handled by blending in prior-season Elo, but not modeled explicitly.
   Small–moderate, mostly early-season.

## 🔸 Minor / situational (low priority)
- **Team-specific home/road splits** beyond league-average HCA (mostly noise
  year to year; altitude already handled).
- **Coaching changes** — small, noisy signal.
- **Motivation / tanking / load-management context** — real late-season, but
  situational and hard to model generally.
- **Style matchups** (e.g., rim protection vs interior offense) — usually worth
  <1 pt and unstable; risk of overfitting.

## ❌ Not worth it (noise or too granular)
- Head-to-head history, referee crews, primetime/TV, specific matchup defenders,
  time-of-day. Individually near-zero and mostly noise.

## Takeaway
The model already captures the **big, stable, well-documented** effects (strength,
home court, rest, travel, altitude, injuries, roster changes). The most defensible
next additions are **cumulative fatigue** and **aging** — both currently blocked
only by missing inputs (a released schedule and player ages), not by the method.
The 3PT-variance idea is the cleanest pure-modeling upgrade: same prediction, more
honest confidence. Everything below that risks adding complexity for noise.
