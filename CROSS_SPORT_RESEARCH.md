# Cross-Sport Modeling Research — what transfers to our NBA model

A survey of prediction models across sports and rating-system theory, and an
honest read on what would actually improve our model vs. add complexity for
little gain.

## What the other sports do

**Soccer — Poisson / Dixon-Coles / xG.** Model each team's *attack* and
*defense* rate separately, predict a full score distribution (not just a
winner), weight recent games more (time-decay), and use **expected goals (xG)**
— a luck-stripped input — instead of raw goals. ([Dixon-Coles](https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/))

**Baseball — Marcel / PECOTA / ZiPS.** Player projections built on three
principles: **weight recent seasons more**, **regress to the mean** by sample
size, and apply an **aging curve**. PECOTA/ZiPS add "comparables" (similar
players' career paths). Punchline: the *dead-simple* Marcel is shockingly hard
to beat — complexity adds only marginal accuracy. ([projection guide](https://library.fangraphs.com/the-projection-rundown-the-basics-on-marcels-zips-cairo-oliver-and-the-rest/))

**NFL — Elo / DVOA / EPA.** 538's Elo adjusts for home, travel, rest, and the
**starting QB** (one dominant player). DVOA is opponent- and situation-adjusted.
Notably, **plain point differential is one of the most predictive metrics —
beating DVOA and EPA.** ([538 NFL Elo](https://github.com/fivethirtyeight/nfl-elo-game))

**Rating theory — Glicko / TrueSkill / Bradley-Terry / Pythagorean.** The modern
systems (Glicko-2, TrueSkill) track not just a rating but its **uncertainty**
(rating deviation): shaky ratings update faster and produce *less confident*
predictions. Pythagorean expectation derives win rate from point margin.
Hierarchical Bayesian versions pool information and beat naive fits on small
samples. ([rating systems review](https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-040722-061813))

**ML / market.** Gradient-boosted trees (XGBoost/CatBoost) **fed Elo-style
ratings as features** are the strongest single learners, and **ensembles** of
Elo + boosting + NN beat any one model. But the **betting market's closing line
is the true ceiling** — the best skill metric is Closing Line Value (beating the
close), not raw win rate. ([ensemble study](https://thexgfootballclub.substack.com/p/which-machine-learning-models-perform), [CLV](https://vsin.com/how-to-bet/the-importance-of-closing-line-value/))

## What this says about *our* model

### ✅ Research confirms our core choices
- **Margin / point differential as the backbone** — the NFL finding (margin beats
  DVOA/EPA) validates our Elo+net-rating approach.
- **Elo power ratings** — the common backbone across every sport, and the key
  feature even inside ML models.
- **Opponent adjustment, home/rest/travel, star-player adjustment** — mirror
  538's proven framework (their QB adjustment ≈ our injury/BPM layer).
- **Keeping it simple** — Marcel beating fancy systems is direct permission to
  *not* over-engineer. Our restraint is a feature.

### 🎯 The highest-value upgrades (borrowed, in priority order)
1. **Track rating uncertainty → an honest confidence band (Glicko/TrueSkill).**
   Our single biggest gap. Every modern rating system carries a *confidence*, we
   carry none. This matters most **right now**: the 2026-27 projection is built
   on brand-new rosters we've never seen play, so its win %s should be *pulled
   toward 50%* (less extreme) until real games arrive. Same idea handles
   high-variance (3-point-heavy) teams. Implementation: a per-team uncertainty
   that widens sigma. Principled, cross-sport-standard, improves calibration.
2. **Split offense and defense (soccer attack/defense, DVOA, KenPom).** Replace
   one net-power number with an *offensive* and *defensive* rating per team.
   Enables style matchups (elite offense vs elite defense) and is strictly more
   informative. We already have points-for / points-against to build it.
3. **Aging + regression-to-mean + multi-season weighting (Marcel).** Our roster
   projection uses one season of BPM at face value. Add an aging curve, shrink
   each player toward the mean by minutes played, and weight the last two seasons
   with recency. This is the workhorse of every baseball system.
4. **Ensemble what we already have.** We *already* trained an XGBoost and a
   logistic model alongside the spread engine — averaging their probabilities is
   a proven, near-free accuracy bump.
5. **Benchmark against the market.** Compare our lines to Vegas closing lines and
   report it. The market is the ceiling; showing we're close is the strongest
   possible credibility statement.

### 🔸 Interesting but lower priority
- **Full score-distribution model (Poisson/Dixon-Coles).** Would let us project
  *totals*, not just winners — a nice feature, bigger build.
- **Hierarchical Bayesian ratings.** More rigorous small-sample handling; largely
  overlaps with #1 and #3 for far more complexity.

## Bottom line
Our model already does the things that matter most across every sport (margin,
opponent-adjusted Elo, home/rest/travel, star availability, calibration) — and
the "simple beats complex" lesson says that's the right instinct. The one thing
*every* modern rating system has that we don't is **uncertainty**, and it's
especially glaring for a fresh-roster projection. If we add one thing, it's an
honest confidence band; offense/defense split and aging are the natural
follow-ups.
