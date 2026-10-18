# Historical data contract and provenance

`games_history.csv` is the committed input snapshot used for reproducible evaluation. The existing project documentation attributes it to earlier Kaggle NBA history combined with later hoopR/ESPN mirrors. The repository does **not** include the raw download/merge script, exact upstream snapshot identifiers, source game IDs or licensing records. This audit verifies internal consistency, not source authenticity or completeness. Do not infer that all rows are regular-season games.

Columns: `date` (game date without tipoff time), `season` (starting year), `home` / `away` (team abbreviations), `home_pts` / `away_pts` (completed scores), and `home_win` (1 iff home points exceed away points). Final scores and labels update Elo **after** the corresponding pre-game features have been recorded.

The 30,905-row snapshot ranges from 2003-10-05 through 2026-04-12. Older seasons include dates in preseason and playoff periods. Seasons 2022–2025 each contain 1,231 rows and end in April. That count alone is not proof of completeness or of a specific game-type mix. No game-type or neutral-site field is available to reconcile the coverage differences reliably.

The validator rejects missing fields, nonfinite numbers, tied completed scores, inconsistent winners, self-matchups, repeated team-days, and chronologically inconsistent season labels. No duplicate team-days, score/label conflicts or tied scores were found in this snapshot. The evaluation artifact records its SHA-256.

To improve upstream reproducibility, preserve immutable source URLs/version IDs and retrieval dates; retain source game IDs, game type and neutral-site flags; record merge/deduplication decisions and licenses; and compare per-season counts to source manifests. Do not silently filter guessed preseason dates: season calendars differ.

Player files and 2026–27 projections are separate scenario inputs. `scripts/build_players.py` currently expects `/tmp/hoopr/nba/player_box/parquet/player_box_2026.parquet`, which is not in the repository. The historical base evaluation does not depend on this file; rebuilding the player pipeline from a clean checkout remains incomplete.

`build_projection.py` uses a hand-written `MOVES` dictionary and rookie assignments without per-transaction citations or verification dates. Treat the resulting 2026–27 roster files as manually specified scenarios, not verified current rosters. Live player refresh does not rebuild the saved projected team power, so live player data and static team power can describe different roster states.
