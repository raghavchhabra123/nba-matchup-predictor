# NBA Matchup Predictor

An interactive **NBA win-probability and what-if dashboard** built with Python and Streamlit. Compare two teams and inspect how team strength, home court, rest, and player availability affect an estimated scoring margin.

[Open the live dashboard](https://nba-matchup-predictor.streamlit.app/)

The deployed demo currently includes projected 2026–27 rosters and travel/altitude adjustments. Those scenario features are separate from the historical base-engine evaluation below; the 68.2% figure should not be interpreted as validation of every deployed feature.

## The analytical question

How can a matchup prediction be both useful and understandable? This project models an expected margin in points, then converts it to a win probability. The dashboard exposes the components rather than presenting an unexplained score.

## Recorded results

The checked-in [evaluation artifact](models/metrics_tier1.json) reports the following results for **2,462 games in the 2024–25 and 2025–26 seasons**:

| Model | Accuracy | Log loss ↓ | Brier score ↓ |
|---|---:|---:|---:|
| Spread engine: Elo + home court + rest | **68.2%** | **0.6044** | **0.2086** |
| Elo only | 67.83% | 0.6062 | 0.2092 |
| Earlier win-rate classifier | 66.0% | 0.6193 | 0.2153 |
| Constant home-win baseline* | 54.91% | 0.6888 | 0.2478 |

These are **saved experiment results**, not a guarantee of future performance. The player-availability extension is not included in this evaluation.

*The evaluation script estimates the constant baseline's probability using seasons from 2015 onward, including the holdout period. Its probability scores are therefore a descriptive comparison, not a strictly training-only benchmark.*

## Method

1. Build sequential Elo ratings from historical games.
2. Fit a margin model using the Elo difference, home court, and back-to-back indicators.
3. Convert the expected margin into a probability using a normal cumulative distribution function.
4. Evaluate accuracy, log loss, Brier score, and reliability bins on later seasons.

The build script uses seasons through 2023 for model fitting; its home-court/rest refit uses 2016–2023. Sequential Elo updates use completed games, while the dashboard's final ratings incorporate the available history.

Rounded fitted effects include a **2.47-point home advantage**, **3.7 points per 100 Elo**, a **−1.78-point home back-to-back effect**, and a **+2.07-point away back-to-back effect** on home margin. The residual scale is approximately **12.51 points**.

See [model building](scripts/build_ratings.py) and [evaluation](scripts/evaluate.py) for the implementation.

## Player-availability scenarios

The dashboard also estimates lineup changes using BPM-based player values and redistributed minutes. This is an exploratory scenario layer, not a separately validated injury-prediction model. Its assumptions should not be confused with observed causal player effects or the holdout results above.

## Run locally

```bash
pip install -r requirements.txt
python -m scripts.build_ratings
python -m scripts.evaluate
streamlit run app.py
```

A fitted engine is included, so rebuilding can be skipped when exploring the existing dashboard. Re-run the scripts to reproduce or audit the saved evaluation in your environment.

## Data and structure

The repository's historical dataset contains 30,905 games spanning 2003–04 through 2025–26. The project combines the earlier Kaggle-based history with later hoopR/ESPN mirrors.

| File or directory | Purpose |
|---|---|
| `app.py` | Streamlit interface and model breakdown |
| `src/elo.py` | Sequential team-strength ratings |
| `src/engine.py` | Margin-to-probability engine |
| `src/ratings.py` | Rest indicators and model specification |
| `src/lineups.py` | Player-availability scenario logic |
| `scripts/build_ratings.py` | Fit and export the engine |
| `scripts/evaluate.py` | Evaluate predictions and calibration |
| `models/engine.json` | Saved model parameters and ratings |
| `models/metrics_tier1.json` | Saved metrics and reliability bins |
| `data/games_history.csv` | Historical game data |
| [`docs/`](docs) | [Model audit](docs/MODEL_AUDIT.md), [research roadmap](docs/ELEVATION_PLAN.md), and [cross-sport research notes](docs/CROSS_SPORT_RESEARCH.md) |

The sidebar's live refresh updates player data through `nba_api`; it does not automatically retrain the Elo engine.

## Limitations and next steps

- Accuracy alone does not establish calibration; inspect reliability bins and probability losses.
- Player scenarios need separate historical validation.
- A cleaner benchmark would fit the constant baseline on training data only.
- Rolling-origin evaluation and uncertainty intervals would strengthen the results.
- Data-source changes, roster changes, and future seasons may shift performance.
- Results here belong to this pipeline. The [earlier exploratory notebook](https://github.com/raghavchhabra123/NBA_HomeCourt_Advantage) uses a different approach and should not be treated as the same experiment.

**Built for analysis and learning, not betting advice.**
