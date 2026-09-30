# Elevating the NBA Matchup Dashboard — Mission & Research-Backed Roadmap

This document lays out what the dashboard should *be*, the honest ceiling of
what's achievable, where the current build falls short of real NBA analytics,
and a prioritized, evidence-backed plan to close the gap. Every number below is
sourced (see the end).

---

## 1. The mission

**Turn any NBA matchup into a transparent, calibrated "what-if" engine:
estimate a team's win probability for a hypothetical or scheduled game, and
show exactly how home court, rest, and player availability move that number —
all denominated in the same point-spread currency the betting market uses.**

Three words define success:

- **Calibrated** — when the app says 65%, the home team should win ~65% of the
  time. Calibration matters more than raw accuracy for a tool people reason with.
- **Decomposable** — a user should see *why* the number is what it is: base team
  strength ± home court ± rest ± who's playing, each in points and probability.
- **Honest** — it states its uncertainty and its ceiling instead of implying
  false precision.

This is deliberately *not* "beat Vegas." It's an explainable teaching/analysis
tool that's correct about the things it claims.

---

## 2. The honest ceiling (so goals stay realistic)

Single NBA games are high-variance. The standard deviation of a game's margin
around the spread is **~11–12 points** [6][7]. That noise caps everyone:

- The best public models and **Vegas closing lines top out around 68–70%
  straight-up accuracy** [2][5]. FiveThirtyEight's Elo alone hit **67.6%**, and
  its RAPTOR-based model **65.8%**, over a 503-game sample [1].
- A well-calibrated NBA model lands near **log-loss 0.60–0.63 / Brier ~0.20**.
  Our current holdout Brier is 0.216 — already in the right neighborhood; the
  win isn't chasing accuracy, it's getting *calibration and decomposition* right.

So the target is not "90% accuracy." It's: match the ~68% ceiling **and** be
genuinely well-calibrated and explainable. That's both ambitious and real.

---

## 3. Where the current build is weakest (and why it matters)

| # | Current approach | Problem | What real analytics does |
|---|---|---|---|
| 1 | Features are all **win-rate** based (last-10, season, rank) | Win-loss record throws away *margin*. Point differential predicts future results better than W-L [8]. | Use **net rating / point differential** and opponent-adjusted power ratings. |
| 2 | No opponent adjustment | Beating cupcakes = beating contenders. No strength-of-schedule. | **Elo** or ridge-regression power ratings that adjust for opponent. |
| 3 | Home court is implicit + a **"mirror-average" hack** to fake neutral court | Fragile, and the learned edge is stale. HCA is now **~54% / ~2.5 pts**, not the old 60% [3][4]. | Model HCA as an explicit **+2.5 pt** term you can toggle to 0. |
| 4 | Player impact is a **homemade** plus-minus + game-score blend | Not opponent-adjusted; invented units. | Anchor to a **RAPM-derived metric (EPM/DARKO/LEBRON)**, in points/100 [9][10]. |
| 5 | Rest is a raw slider, effect learned weakly | Under-weights a real, measurable effect. | Encode it: **back-to-back ≈ −2 pts, ~43.6% win vs 51.8% rested** [11][12]. |
| 6 | Win prob comes straight from a classifier | Can't cleanly add HCA + rest + injuries together | Work in **point-spread space**, convert once via the normal CDF (SD≈12) [6][7]. |
| 7 | Reports accuracy/AUC only | No calibration check, no baseline to beat | **Reliability diagram, log-loss, vs. a market/Elo baseline.** |
| 8 | No injuries, travel, pace, altitude | Missing the context that actually moves games | Real **injury report**, travel/altitude, pace for totals. |

---

## 4. The single most important architectural change: go to point-spread space

Right now HCA, rest, and player toggles are bolted onto a win-probability
classifier in different, ad-hoc ways. The fix that makes *everything else*
principled is to predict a **point spread (expected margin)** first, then
convert to win probability **once** at the end:

```
expected_margin =  power_rating(home) − power_rating(away)
                 + HOME_COURT            # +2.5 if home court ON, 0 if neutral
                 + REST_ADJ              # e.g. −2.0 if home on a back-to-back
                 + PLAYER_ADJ            # sum of impacts (points) for who's in/out

win_prob_home   =  Φ( expected_margin / 12 )     # normal CDF, SD ≈ 12
```

Why this is the keystone:

- **Everything lives in the same unit (points).** Home court, rest, and a star
  sitting are all just point adjustments that add up — no more mixing a logit
  hack with a plus-minus blend. This is exactly how Vegas and 538 operate.
- **The toggles become honest and legible.** "Neutral court" literally means
  set the +2.5 to 0. "SGA out" literally subtracts his ~5 points [13].
- **It's independently checkable.** Elite players are worth **4–5.5 pts** on the
  spread (Spurs went from −1.5 to −5.5 with Wembanyama) [13]; HCA ~2.5 [4]; B2B
  ~2 [11]. You can eyeball whether the app agrees with reality.

Power ratings can come from **Elo** (538's MOV-adjusted K-factor:
`K = 20(MOV+3)^0.8 / (7.5 + .006·ΔElo)` [14]) and/or a **ridge regression on net
rating**. Keep the current classifier as a second opinion, but make the
spread-based engine the backbone.

---

## 5. Prioritized roadmap

### Tier 1 — Foundation (biggest, most defensible accuracy + honesty gains)
1. **Net-rating / point-differential features** instead of pure win-rate [8].
2. **Elo power ratings** with 538's MOV multiplier and autocorrelation fix [14],
   rebuilt from the 30k-game history already in the repo.
3. **Point-spread architecture** (Section 4) as the prediction backbone.
4. **Explicit, calibrated home court = +2.5 pts**, toggleable to 0 [3][4].
5. **Realistic rest model**: B2B ≈ −2 pts / derive from schedule when available [11][12].
6. **Evaluation upgrade**: calibration/reliability curve, log-loss, and a
   **baseline comparison** (Elo-only and a naive "home always wins ~54%") so
   improvements are provable, not asserted.

### Tier 2 — Player realism
7. **Anchor player impact to a published RAPM-derived metric** (DARKO updates
   daily and is scrapeable; EPM/LEBRON are the field standard) instead of the
   homemade blend [9][10]. Keep the box-score version as a fallback.
8. **Minutes redistribution**: when a starter sits, his minutes flow to bench
   players at *their* impact, not to a generic replacement — this is what makes
   "load management" scenarios realistic.
9. **Replacement level done right** (a bench player ≈ −2 pts/100, not 0).

### Tier 3 — Real NBA context
10. **Live injury report** from the official NBA feed (submitted by team medical
    staff, 5 p.m. day-before deadline) so "who's out" can auto-populate [15].
11. **Travel & altitude**: distance, time-zone changes, and Denver/Utah altitude
    as small spread terms.
12. **Strength-of-schedule / recency weighting** baked into power ratings.
13. **Pace** so the app can also project a total (points), not just a winner.

### Tier 4 — Product & trust
14. **"What moved the line" breakdown** — a waterfall: base ± HCA ± rest ± players.
15. **Uncertainty band** on the win probability (games are ±12 pts of noise).
16. **Backtest view** — show the model's calibration on the last two seasons
    inside the app, next to Vegas/Elo, so users trust the number.
17. **Auto-switch to the 2026-27 schedule** the moment it releases: real
    matchups, real rest, real back-to-backs instead of hypothetical inputs.

---

## 6. What I'd build first

Tier 1 is the highest-leverage, most factual, and fully buildable **today** from
data already in the repo — no paid APIs. It replaces the shakiest parts (win-rate
features, the mirror-average HCA hack) with the point-spread + Elo backbone that
professional models use, and it adds the calibration/baseline evidence that makes
every later claim provable.

Recommended sequence: **Tier 1 → 7/8 (real player metric + minutes) → 10 (live
injuries) → 14/16 (decomposition + backtest UI).**

---

## Sources

1. [FiveThirtyEight forecast accuracy: Elo 67.6% vs RAPTOR 65.8%](https://andrewkyne.wordpress.com/2020/01/04/fivethirtyeight-nba-forecast-accuracy-raptor/)
2. [Model accuracy 60–70% straight-up (survey)](https://cs229.stanford.edu/proj2013/ChengDadeLipmanMills-PredictingTheBettingLineInNBAGames.pdf)
3. [Home win % fell from ~60% to ~54% (Yahoo Sports)](https://sports.yahoo.com/fact-or-fiction-is-home-court-advantage-in-the-nbas-regular-season-dead-194958543.html)
4. [HCA ≈ 2.0–3.0 pts; closing-line ~2.05 (VSiN)](https://vsin.com/nba/nba-true-home-and-road-court-advantage/)
5. [Vegas spread accuracy / miss magnitude](https://github.com/NBA-Betting/NBA_AI)
6. [SD of NBA margin ≈ 12 points (Winston)](https://waynewinston.com/wordpress/p_2333/)
7. [Updated NBA win-probability calculator (inpredictable)](https://www.inpredictable.com/2015/02/updated-nba-win-probability-calculator.html)
8. [Point differential predicts future wins better than record (Nylon Calculus)](https://fansided.com/2017/09/18/nylon-calculus-expected-win-totals-distribution/)
9. [RAPM is the backbone of EPM/DARKO/LEBRON/BPM](https://medium.com/@johnchenmbb/calculating-rapm-steps-1-and-2-of-my-summer-plan-1a78e1476b1f)
10. [Best NBA impact metrics overview](https://www.cryptbeam.com/2021/05/21/the-10-best-nba-impact-metrics/)
11. [Rested 51.8% vs back-to-back 43.6%; scoring −3–5% (Data Jocks / Medium)](https://thedatajocks.com/the-stats-behind-back-to-back-nba-games/)
12. [Role of rest in home-court advantage (Wharton)](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Nba.pdf)
13. [Elite players worth 4–5.5 pts on the spread (Wembanyama example)](https://dallashoopsjournal.com/p/injuries-reshape-nba-win-probability-betting-markets-competitive-balance/)
14. [538's Elo MOV multiplier & autocorrelation formula](https://andr3w321.com/elo-ratings-part-2-margin-of-victory-adjustments/)
15. [Official NBA injury report mechanics & data access](https://github.com/mxufc29/nbainjuries)
