# NBA Matchup Predictor

An interactive NBA pre-game probability dashboard built with Python and Streamlit. Explore how team strength, home court, rest and player availability change an estimated scoring margin.

[Open the live dashboard](https://nba-matchup-predictor.streamlit.app/) · [Technical audit](docs/EVALUATION_AUDIT.md) · [Data provenance and limits](data/README.md)

## What this project demonstrates

A sequential Elo model produces team-strength features before each game. A linear margin model adds home court and back-to-back indicators, then a normal CDF converts the margin to a home-win probability. The dashboard breaks predictions into understandable components.

The historical base engine is evaluated separately from the **exploratory** roster, injury, travel and altitude scenarios. Those scenarios are not validated by the scores below. The live dashboard may run a different revision until these changes are merged and deployed.

## Reproduced evaluation

The [evaluation report](models/metrics_tier1.json) covers **2,462 games in seasons 2024–25 and 2025–26**. Fitted coefficients, classifier preprocessing and baseline probabilities use only seasons through 2023–24. Elo updates after each completed game, as it would during a season.

| Model | Accuracy | Log loss ↓ | Brier ↓ | ROC-AUC |
|---|---:|---:|---:|---:|
| Spread engine: Elo + home court + rest | 67.79% | **0.6035** | **0.2082** | **0.7306** |
| Elo only | **67.83%** | 0.6062 | 0.2092 | 0.7292 |
| Win-rate logistic regression | 65.68% | 0.6207 | 0.2159 | 0.7115 |
| Training home-rate baseline | 54.91% | 0.6890 | 0.2479 | 0.5000 |

The spread engine's accuracy difference from Elo is **−0.04 percentage points**, with a paired game-date bootstrap 95% interval of **−0.97 to +0.92 points**. This does not establish an accuracy improvement over Elo. Its probability losses are slightly lower in this sample; no significance claim is made for those differences. Date resampling does not capture dependence across dates or model-selection uncertainty.

The report also includes separate season results, reliability-bin counts, average precision and three expanding-window development folds (2021, 2022, 2023). All models in a window use the same evaluation games. Per-game probabilities are saved in [reports/holdout_predictions.csv](reports/holdout_predictions.csv).

**These seasons have already been inspected during project development.** Treat this as a retrospective chronological evaluation, not a pristine, untouched final test. A future frozen forecast log is the next step. The previously reported 68.2% artifact had coefficients inconsistent with the checked-in engine; these results replace it.

## Reproduce locally

Python 3.10 or 3.11 is recommended. From the repository root:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements-eval.txt
python -m pytest -q
python -m scripts.build_ratings
python -m scripts.evaluate
python -m scripts.stress_test
```

No API keys or network data downloads are needed for evaluation. `requirements-eval.txt` pins the numerical stack; the report records Python/package versions and the input CSV SHA-256. Re-running evaluation deterministically rebuilds benchmarks from training data and never loads the deployment classifiers. Minor floating-point differences across platforms are possible.

To run the dashboard, additionally install `requirements.txt`, then run `streamlit run app.py`. Live refresh and chat use optional external services; historical evaluation does not. To rebuild the optional legacy deployment classifiers, install `requirements-dev.txt` and run `python -m scripts.train_model`. Those full-data artifacts must never be used as holdout estimators.

## Repository guide

| Path | Purpose |
|---|---|
| `app.py` | Dashboard, scenario controls and quality panel |
| `src/elo.py` | Sequential pre-game Elo |
| `src/features.py` | Shifted form and prior-day standings features |
| `src/validation.py` | Game integrity and temporal split contracts |
| `scripts/build_ratings.py` | Shared training-only margin fit and engine export |
| `scripts/evaluate.py` | Fresh fits, baselines, rolling evaluation and uncertainty |
| `tests/` | Leakage, data integrity, metric and residual-scale regression tests |
| `.github/workflows/evaluation.yml` | Automated tests, rebuild and evaluation artifacts |
| `data/games_history.csv` | Committed historical snapshot; see provenance limitations |
| `models/engine.json` | Base coefficients plus final-history ratings for future scenarios |

## Limits and next steps

- The snapshot has 30,905 rows, with mixed game coverage across seasons. Raw ingestion, stable source game IDs, game types and neutral-site flags are missing. Its upstream completeness has not been independently verified.
- Designated home teams are treated as having home court, including potential neutral-site games. This is a modeling limitation.
- Standings and recent form use completed results only; missing values are imputed within training pipelines. Date-only data cannot support tipoff-time injury availability claims.
- Roster assignments are manual, without transaction-level source citations; treat them as scenarios, not verified current rosters. Live player refresh does not rebuild saved projected team power. Roster/BPM projections and hand-set travel/altitude effects need separate historical validation. Existing stress checks establish internal consistency, not predictive accuracy or causal effects.
- Priorities: reconstruct source provenance and game types, add neutral venues, freeze forecasts before tipoff, then evaluate scenario extensions against the base engine.
- The [earlier exploratory notebook](https://github.com/raghavchhabra123/NBA_HomeCourt_Advantage) is a different experiment with same-day standings leakage risk; its 77.9% headline is not a validated comparison to this pipeline.

Built for analysis and learning, not betting advice.
