# START HERE — NBA Matchup Predictor

Orientation for a new chat or a human picking this project up cold.

## What it is
A Streamlit app that answers **"if these two NBA teams played, who wins — and
why?"** It predicts an expected point margin from opponent-adjusted power
ratings, adds interpretable adjustments (home court, rest, travel, player
availability), and converts to a **calibrated win probability**. A left-side
selector (Casual / Fan / Analyst) controls how much depth is shown.

## Run it
```bash
cd matchup_dashboard
pip install -r requirements.txt        # first time
streamlit run app.py
```
(Or double-click `run.command` on macOS — it sets up a venv and launches.)

## The 60-second model
1. **Data:** 30,905 games, 2003–2026 (Kaggle + ESPN/hoopR mirrors).
2. **Elo power ratings:** 538-style, margin-of-victory + autocorrelation, season
   carryover.
3. **Point-spread regression:** margin ~ Elo diff + home + back-to-back →
   home court **+2.5**, B2B **−1.8**, **3.7 pts/100 Elo**, σ **12.5**.
   Win prob = Φ(margin / σ).
4. **Players:** BPM (published anchors + calibrated estimate, recentered to real
   net ratings) + a minutes-redistribution model (depth matters).
5. **Context:** travel/altitude terms; live ESPN injury feed auto-sits players.
6. **Eval:** chronological holdout (2024-26, 2,462 unseen games): **68.2%
   accuracy, 0.60 log-loss**, well-calibrated. 25-check automated test suite.

## File map
```
app.py                     Streamlit UI (Casual/Fan/Analyst layers)
src/elo.py                 Elo power ratings
src/ratings.py             rest/B2B flags, rolling net rating, model spec
src/engine.py              SpreadEngine: margin -> win prob + breakdown
src/lineups.py             minutes-redistribution player model
src/bpm_anchors.py         published Basketball-Reference BPM by player
src/travel.py              arena coords, distance/timezone/altitude terms
src/injuries.py            ESPN live injury feed
src/summary.py             plain-English "The Take" generator
src/live.py                nba_api live refresh
scripts/build_ratings.py   build Elo + fit the point-spread engine
scripts/build_players.py   build player BPM table
scripts/evaluate.py        holdout metrics + calibration
scripts/stress_test.py     25-check model sanity suite
models/                    fitted coefficients + metrics
data/                      games history, ratings, players, teams
```

## For the résumé
- Full writeup with bullets + interview Q&A: **`PROJECT_WRITEUP.md`**.
- Mission + research-backed roadmap (Tiers 1–4): **`ELEVATION_PLAN.md`**.
- Headline: matches the ~68% accuracy ceiling of Vegas / FiveThirtyEight, with
  calibrated probabilities and a full automated test suite.

## Status
- **Done:** Elo + point-spread engine, calibration/eval, BPM player model with
  depth, travel/altitude, live injuries, layered UI, dark theme.
- **Known limits:** single-game variance caps accuracy ~68%; high-usage guards
  on deep teams are under-valued vs the betting market. Both documented.
- **Not built (Tier 4 ideas):** uncertainty band on the win %, season simulator,
  optional LLM chatbot.

## To rebuild everything from scratch
```bash
python -m scripts.build_ratings    # Elo + spread engine
python -m scripts.build_players    # player BPM table (needs hoopR data)
python -m scripts.evaluate         # holdout metrics
python -m scripts.stress_test      # sanity checks
```
