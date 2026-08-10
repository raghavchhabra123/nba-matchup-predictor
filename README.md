# 🏀 NBA Matchup Win-Probability Dashboard

A transparent, calibrated **what-if engine** for NBA matchups. Pick any two
teams, toggle home court, rest, and player availability, and see the projected
win probability — with a full breakdown of *why* it is what it is, every effect
measured in points.

Built on (and a major upgrade to) the
[NBA_HomeCourt_Advantage](https://github.com/raghavchhabra123/NBA_HomeCourt_Advantage)
pipeline. See `ELEVATION_PLAN.md` for the researched mission and full roadmap.

## Run it

```bash
pip install -r requirements.txt
python -m scripts.build_ratings   # build Elo + point-spread engine (once)
python -m scripts.evaluate        # holdout metrics + calibration (optional)
streamlit run app.py
```

(The repo ships with the engine already built, so you can skip straight to
`streamlit run app.py`.)

## How it works — the point-spread backbone

Instead of feeding a black-box classifier, the engine predicts an **expected
margin in points**, then converts to a win probability once at the end:

```
expected_margin = 0.037 · (Elo_home − Elo_away)   # neutral power-rating gap
                + 2.5   if home court is ON        # fitted home-court advantage
                − 1.8   if home is on a back-to-back
                + player_points                    # from availability toggles
P(home win)     = Φ(expected_margin / 12.5)        # normal CDF, σ from the data
```

Because home court, rest, and injuries all live in the **same unit (points)**,
they simply add up — the way Vegas and FiveThirtyEight build a number. The
dashboard shows the full waterfall (power ± home ± rest ± players → margin).

Every coefficient was **fitted from 30,905 games and matches published NBA
research**:

| Effect | This model | Real-world benchmark |
|---|---|---|
| Home-court advantage | **+2.5 pts** | ~2.0–3.0 pts; betting closing line ≈ 2.05 |
| Back-to-back penalty | **−1.8 pts** | ~−2 pts; B2B teams win ~43.6% vs 51.8% rested |
| Elo → points | **3.7 pts / 100 Elo** | 538 ≈ 3.6 pts / 100 Elo |
| Margin noise (σ) | **12.5 pts** | SD of NBA margin ≈ 11–12 pts |

## Power ratings (Elo)

Neutral team strength via FiveThirtyEight-style Elo: a margin-of-victory
multiplier with the autocorrelation correction (blowouts help but don't
runaway-inflate top teams), home court applied only at prediction time, and 75%
season-to-season carryover with mean reversion. Rebuilt over all 30,905 games.

## Player availability (Tier 2)

Player value uses **BPM (Box Plus/Minus)** — points per 100 possessions above
league average, a published, RAPM-informed metric. Star players use the real
Basketball-Reference 2025-26 BPM (`src/bpm_anchors.py`); everyone else gets a
box-score + on-court plus/minus estimate calibrated to those anchors
(`scripts/build_players.py`).

When a player sits, a **minutes-redistribution model** (`src/lineups.py`) flows
his minutes to the rest of the rotation (capped at 40 mpg), with any overflow to
a replacement-level player (BPM −2.0). A lineup's expected margin ≈ Σ BPM × min/48,
so the swing is the difference between the healthy and depleted lineups. This
makes **depth matter**: OKC losing Shai barely moves (elite bench absorbs it),
while Denver losing Jokić craters (thin behind him) — mirroring reality. Swings
are calibrated so an MVP-level absence lands near the market's ~4–6 points.

## Results (strictly out-of-sample: 2024-25 & 2025-26, 2,462 games)

| Model | Accuracy | Log-loss | Brier |
|---|---|---|---|
| **Spread engine (Elo + HCA + rest)** | **68.2%** | **0.604** | **0.209** |
| Elo only | 67.8% | 0.606 | 0.209 |
| Win-rate classifier (v1) | 66.0% | 0.619 | 0.215 |
| Naive "home wins" (56.5%) | 54.9% | 0.689 | 0.248 |

68% is the realistic ceiling for pre-game models — Vegas and FiveThirtyEight
land there too. The bigger win is **calibration**: when the app says 65%, the
home team really wins ~63% of the time (see the reliability chart in the app).

## Data

- `data/games_history.csv` — 30,905 games, 2003-04 → 2025-26 (original repo
  Kaggle data through 2021-22, then hoopR/ESPN mirrors).
- `data/elo_ratings_2026.csv` — final neutral Elo + season net rating per team.
- `data/players_2026.csv` — per-player 2025-26 stats + impact estimates.
- **Live refresh** (sidebar) pulls current player stats from stats.nba.com via
  `nba_api` (free, no key). Note: the Elo engine ships pre-built on completed
  data; live refresh updates player availability. Rebuild ratings with
  `python -m scripts.build_ratings` once a new season has games.

## Structure

```
app.py                     # Streamlit dashboard (point-spread engine)
src/elo.py                 # 538-style Elo power ratings
src/ratings.py             # rest/B2B flags, rolling net rating, model spec
src/engine.py              # SpreadEngine: margin -> win prob, with breakdown
src/features.py            # v1 leak-free win-rate features (baseline classifier)
src/predict.py             # v1 prediction helpers (kept for reference)
src/live.py                # nba_api live refresh
scripts/build_ratings.py   # build Elo + fit the point-spread engine
scripts/evaluate.py        # holdout metrics + calibration vs baselines
scripts/train_model.py     # retrain the v1 classifier
models/engine.json         # fitted coefficients + final ratings
models/metrics_tier1.json  # holdout metrics + reliability table
ELEVATION_PLAN.md          # mission + researched roadmap (Tiers 1-4)
```

For analysis and fun — not betting. 🙂
