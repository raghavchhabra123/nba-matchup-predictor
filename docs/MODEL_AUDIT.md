# Model coverage and evidence

See the [code and evaluation audit](EVALUATION_AUDIT.md) for findings, fixes and validation, and the [data contract](../data/README.md) for provenance limits.

| Component | Implementation | Evidence status |
|---|---|---|
| Team strength | Sequential Elo built before each game | Included in historical evaluation |
| Home court | Recent-era fitted intercept | Included; neutral-site flags are missing |
| Back-to-back rest | Fitted home/away indicators | Included in historical evaluation |
| Roster projection | Current player BPM blended with regressed Elo | Exploratory; no matched historical evaluation |
| Player availability | BPM and redistributed minutes | Internally stress-tested; not validated injury effects |
| Travel and altitude | Hand-set adjustments | Internally stress-tested; not historically validated |
| Aging, schedule congestion, coaching, motivation | Not explicitly modeled | No quantified claim of incremental benefit |

The base engine has similar accuracy to Elo alone and slightly better probability losses in the current retrospective test. This is not evidence that each dashboard adjustment is accurate or causal. The previous version of this document characterized several effects as “covered well” without corresponding predictive validation; those claims are superseded.

Next steps: establish raw-data reproducibility and game-type/venue coverage, log forecasts before tipoff, then evaluate each proposed extension against the unchanged base on temporal development folds and a new prospective test.
