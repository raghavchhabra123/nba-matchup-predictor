# Evaluation audit — October 17, 2026

Scope: public repositories under `raghavchhabra123`, focusing on the maintained `nba-matchup-predictor` and its predecessor `NBA_HomeCourt_Advantage`. Baseline revision: `22aec84` of the maintained project. The account has eight visible repositories; the profile and historical notebook both point visitors to the maintained dashboard. No Claude collaboration was used.

## Findings and changes

| Priority | Finding at baseline | Resolution in this branch |
|---|---|---|
| High | `scripts/evaluate.py` loaded `models/logistic.joblib`, but `scripts/train_model.py` exports it after fitting **all** rows. Rebuilding could contaminate classifier holdout scores. | Evaluator always creates a fresh logistic pipeline trained strictly before the test window. It never reads deployment pickles. |
| High | `src/features.py` filled missing values with full-frame medians before splitting. Future rows could change past inputs. | Leave NaNs for training-fitted `SimpleImputer` in both evaluation and training. Prefix/mutation tests cover leakage. |
| High | Training used “not in test seasons,” admitting later seasons if data grew. | Shared temporal split allows only seasons before the earliest test season and checks date boundaries. |
| Medium | Home-rate baseline included holdout outcomes. | Estimate from 2015 through the training cutoff only and report probability/sample size. |
| Medium | Saved metrics used HCA 2.470, home B2B −1.779 and away B2B +2.067, while the checked-in engine used 2.031, −2.047 and +2.509. | Rebuild and evaluate using one shared fit function. Old 68.2% metrics are superseded. |
| Medium | Residual sigma described the all-history coefficients, not the hybrid recent-era HCA/rest coefficients exported for prediction. | Compute residuals with the actual rounded coefficients. |
| Medium | Daily standings forward-filled **pre-game** win rates, leaving idle teams one result behind. | Carry post-game cumulative rates forward, then lag the entire date table before ranking. |
| Medium | The UI called calibration “On target” and 68% a Vegas/FiveThirtyEight ceiling without a matched benchmark. | Show actual accuracy, Elo comparison and Brier score; qualify calibration and scenario coverage. |
| Medium | No automated leakage/data tests or CI; broad dependency lower bounds; no per-game evaluation output. | 14 regression tests, CI, pinned numerical environment, input hash, environment metadata and per-game probabilities. |
| Open | No raw historical ingestion script, source IDs, game type or neutral-site flags. Player rebuild depends on a local `/tmp/hoopr` file. | Documented in `data/README.md`; source reconstruction requires verified upstream snapshots. No guessed replacement data was introduced. |

## What the results establish

On the committed snapshot, the rebuilt base engine reaches 67.79% accuracy, 0.6035 log loss, 0.2082 Brier and 0.7306 ROC-AUC on 2,462 evaluation games. Elo alone reaches 67.83% accuracy. The paired accuracy interval includes zero. The spread model has slightly better probability losses but this report does not establish a statistically significant improvement.

Each evaluation window freezes model coefficients, scaling and imputation at its training cutoff. Elo and form update sequentially after completed games inside the evaluation window. This is realistic for game-by-game forecasts; it is **not** a forecast of an entire season made before opening night. Final-history Elo and projected roster power are not used to score historical games.

Development folds refit on seasons before 2021, 2022 and 2023 respectively. The pooled final window keeps coefficients frozen through 2023 for both 2024 and 2025. Per-season scores use those same frozen coefficients. Hyperparameters were not newly tuned to these results. Since prior work already inspected the final seasons, they are not an untouched model-selection holdout.

All reliability bins with observations are retained. Small bins are uncertain. The paired bootstrap resamples whole game dates with seed 42, preserving same-day dependence but not longer-range dependence. Reported intervals do not include model-selection uncertainty.

## Earlier notebook: confirmed leakage

The predecessor notebook merges standings with `allow_exact_matches=True`, allowing same-day end-of-day standings. An audit of its committed CSVs (after game-ID deduplication and team/date standings deduplication) found 24,770 home games where standings increased by exactly one game from the prior day; **all 24,770 changes matched that day's result**. Thus same-day standings can directly incorporate the target. Full-data median imputation is a second leakage path. The 77.9% headline cannot support a pre-game forecasting claim.

The old notebook also selects the “best” model using the test metrics, then inspects importance on that same test set. Its reported metrics belong to an exploratory, contaminated evaluation and are not comparable to the maintained model's corrected benchmark. The notebook should be kept only as an explicitly labeled historical artifact until rebuilt and independently evaluated.

## Verification and remaining work

Local verification: the complete historical rebuild/evaluation, 14 pytest regression cases, and the existing backend stress suite passed. Evaluation was repeated with byte-identical metrics and prediction outputs. Streamlit AppTest rendered both the default view and Analyst quality panel without exceptions. CI repeats numerical tests, engine build, evaluation and stress checks, then uploads the report and predictions.

The stress suite checks signs, bounds and internal consistency, not the empirical magnitude of player/travel effects. Tests cannot certify source completeness, tipoff-time availability, or generalization to future seasons.

Prioritize upstream provenance, source reconciliation and neutral-site handling before adding model complexity. Then freeze pre-tipoff predictions and evaluate calibration, probability losses, season stability and incremental value of each scenario extension. Keep the public profile aligned with reproduced evidence, with no market-performance claims absent matched historical odds.
