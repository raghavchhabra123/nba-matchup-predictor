# NBA Matchup Predictor — Modeling Writeup

A résumé/interview-ready explanation of how the model works, the decisions
behind it, and how to talk about it.

---

## One-sentence summary

An NBA matchup win-probability engine that predicts an **expected point
margin** from opponent-adjusted power ratings, adds interpretable adjustments
for home court, rest, travel, and player availability, and converts the margin
to a **calibrated win probability** — reaching ~68% out-of-sample accuracy, the
practical ceiling for pre-game models.

---

## 1. Data (30,905 games, 2003–2026)

- **Historical games:** the original project's Kaggle dataset (2003–2022),
  extended with ESPN/hoopR mirrors (2022–2026). Team abbreviations harmonized
  (e.g., `GS→GSW`, `NO→NOP`), duplicates dropped, sorted chronologically.
- **Players:** 2025-26 per-player box scores (hoopR) plus published
  **Basketball-Reference BPM** for ~120 rotation players used as anchors.
- **Context:** arena coordinates/timezone/altitude for 30 teams; live injuries
  from ESPN's public feed; optional live team/player refresh via `nba_api`.

## 2. Power ratings — FiveThirtyEight-style Elo

A single *neutral* team-strength number per team, updated game-by-game:

- **Margin-of-victory multiplier** so blowouts move ratings more than
  one-possession wins — but with an **autocorrelation correction** so favorites
  running up the score don't inflate infinitely.
- **Home court applied only at prediction time** (the rating itself stays
  location-neutral), so it never double-counts.
- **Season carryover:** each team keeps 75% of its rating into the next season
  and regresses 25% toward the league mean.

Elo was chosen because it opponent-adjusts automatically and weights recent
form — it beats raw win% or season averages.

## 3. The core: a point-spread model

Instead of feeding a black-box classifier, the engine predicts an **expected
margin in points**, then converts once at the end:

```
expected_margin = b·(Elo_home − Elo_away)   # power gap
                + HOME_COURT                 # +2.5 if home, 0 if neutral
                + REST                        # back-to-back penalty
                + PLAYERS                     # availability (points)
                + TRAVEL                      # trip + altitude
win_prob_home   = Φ(expected_margin / σ)      # normal CDF, σ ≈ 12.5
```

The coefficients are **fit by linear regression** of actual margin on Elo
difference, a home indicator, and back-to-back flags (chronological train
split, seasons ≤ 2023-24). The fitted values landed exactly where published NBA
research says they should — which is the validation:

| Effect | Fitted | Real-world benchmark |
|---|---|---|
| Home court | **+2.5 pts** | ~2–3; betting close line ≈ 2.05 |
| Back-to-back | **−1.8 pts** | ~−2; B2B teams win ~43.6% vs 51.8% |
| Elo → points | **3.7 / 100** | 538 ≈ 3.6 |
| Margin noise σ | **12.5** | SD of NBA margins ≈ 11–12 |

**Why this design matters:** every effect lives in the same unit (points), so
they're additive, independently checkable, and legible to a user — the way
Vegas and 538 build a number. It's the difference between "the model says 63%"
and "63% because +1.3 power, +2.5 home court, +0.6 travel."

## 4. Player impact — BPM + minutes redistribution

- **Metric:** Box Plus/Minus (points per 100 possessions above average).
  Published values for stars; a box-score + on-court plus/minus **estimate** for
  everyone else, calibrated to the anchors, then **recentered per team so each
  team's minutes-weighted BPM equals its actual net rating** (ties the player
  model to real results — this fixed a systematic bias).
- **When a player sits**, his minutes flow to the rest of the rotation (capped
  at 40 mpg), with overflow to a replacement-level player (BPM −2.0). Team value
  ≈ Σ BPM × minutes/48; the change vs full strength is the point swing.
- **Result:** depth matters. Losing Shai only costs OKC ~5 (elite bench absorbs
  it); losing Jokić costs Denver ~7 (thin behind him) — matching reality.

## 4b. Predicting a *new* season — the offseason projection

Last season's ratings are stale the moment free agency starts. The 2026
offseason moved half the league (Giannis → Miami, LeBron & Jaylen Brown →
Philadelphia, Ja Morant → Portland, Kawhi → Toronto, plus the draft). So for
2026-27 the model builds a **preseason projection** (the way FiveThirtyEight's
CARM-Elo does):

1. Take each player's 2025-26 BPM and **reassign him to his current team** after
   every trade/signing; add the top draft rookies.
2. Each team's roster-projected net rating = Σ BPM · minutes/48 over its rotation.
3. **Blend** that with the team's regressed prior-season Elo (converted to
   points) — keeping season-tested signal while reflecting who's actually on the
   roster now.

Result: Milwaukee's rating collapses after losing Giannis, Miami's and
Philadelphia's jump, and the app predicts the *upcoming* season rather than the
one that already happened. (Honest caveat: a fresh-roster projection can't be
back-tested until games are played; the 68% figure is the Elo engine's measured
accuracy.)

## 5. Context terms

- **Travel/altitude:** great-circle distance, timezone shift (eastward penalized
  more than westward, per circadian research), and a Denver/Utah altitude bonus
  — only deviations from average count, so typical games are ~0.
- **Live injuries:** ESPN feed auto-sits Out/Doubtful players and badges status.

## 6. Evaluation & testing

- **Strict chronological holdout:** 2024-25 and 2025-26 (2,462 games never seen
  in training).
- **Results:** 68.2% accuracy · 0.604 log-loss · 0.209 Brier. Beats the
  win-rate classifier (66.0%) and a naive "home always wins" baseline (54.9%),
  and matches the ~68% ceiling that Vegas/538 also hit.
- **Calibration:** a reliability curve confirms probabilities are honest (when
  it says 65%, home teams win ~63%) — arguably more important than accuracy for
  a tool people reason with.
- **25-check automated stress test** (`scripts/stress_test.py`): probability
  bounds, power-rating symmetry, monotonicity, correct signs for every
  adjustment, depth effects, and edge cases (e.g., removing a sub-replacement
  player *helps* a team).

## 7. Decisions worth calling out in an interview

- **Leak-free features:** shifted rolling windows and a chronological train/test
  split — no future information leaks into predictions.
- **Point-spread space** for additivity and interpretability.
- **Calibration over raw accuracy** as the success metric.
- **Anchoring estimates to published metrics** (BPM) and **recentering to real
  net ratings** to remove bias — a concrete example of validating a model
  against ground truth.
- **Honest about limits:** high-usage guards on deep teams are under-valued vs
  the market (minutes don't redistribute as cleanly as the model assumes);
  single-game variance (~12 pts) caps everyone near 68%.

---

## Résumé bullets (adapt freely)

- Built an **NBA matchup win-probability engine** (Python, pandas, scikit-learn,
  Streamlit) over **30,905 games (2003–2026)**, combining FiveThirtyEight-style
  **Elo power ratings** with a **point-spread regression** converted to
  calibrated probabilities via a normal CDF.
- Achieved **68% out-of-sample accuracy (0.60 log-loss)** on two fully held-out
  seasons — matching the practical ceiling of Vegas and FiveThirtyEight — with
  **well-calibrated** probabilities verified by a reliability curve.
- Engineered **interpretable, additive point adjustments** for home court, rest,
  travel/altitude, and player availability (a **BPM-based minutes-redistribution
  model**), each validated against published NBA research.
- Integrated **live data** (nba_api, ESPN injury feed) and shipped a **layered
  UI** (casual → analyst) backed by a **25-check automated model test suite**.

## Likely interview questions (and short answers)

- *Why Elo over a classifier?* Opponent-adjusts automatically, weights recent
  form, and stays interpretable; the classifier on win-rate features scored
  lower (66% vs 68%).
- *Why predict margin then convert, instead of predicting the probability
  directly?* Additivity — home court, rest, injuries, and travel are all point
  effects that sum, and each is independently sanity-checkable.
- *How do you know it's not overfit?* Strictly chronological holdout of unseen
  future seasons; results match independent public benchmarks; calibration
  curve is on the diagonal.
- *Biggest limitation?* Single-game variance caps accuracy ~68%; the player
  model under-weights star usage on deep teams. Both are documented.
