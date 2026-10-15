# Pre-registered final evaluation (written 2026-10-16, before any test/cafe2 run)

Sealed splits: `test` (378 dishes: official depth_test minus cross-split re-scans and bad labels) and `cafe2` (221 dishes,
cafe2 dishes in no official split; totals recomputed from ingredient rows). No-food images: none in these splits.
Each candidate below is run ONCE per split with `--final`; no candidate is added, changed or dropped after seeing results.
Metric of record: mae_pct_of_mean (MAE as % of mean truth, Nutrition5k Table 3 convention). Also reported: median APE,
bias, tercile bias, log-kcal r, log-mass r, $/dish.

| id | model | harness | role |
|---|---|---|---|
| h0_direct | Haiku 5.5 | plain direct prompt | plain baseline |
| h2_plate_scale | Haiku 5.5 | plate-as-ruler prompt | strong single-prompt baseline |
| gen2/compA_v2 | Haiku 5.5 | evolved (gen2 composer A, 6 fitted constants) | best on select |
| gen2/compA_v4 | Haiku 5.5 | evolved (gen2 composer A, 2 fitted constants) | primary evolved system |
| gen2/compB_v1 | Haiku 5.5 | evolved, zero fitted constants | transfer-oriented system |
| gen2/compC_v5 | Haiku 5.5 | evolved, 2 calls | cost-efficient system |
| sonnet/b0_direct, sonnet/b2_plate_scale | Sonnet 5.5 | plain / plate-as-ruler | larger-model plain baselines |
| opus/b0_direct_opus, opus/b2_plate_scale_opus | Opus 5.5 | plain / plate-as-ruler | largest-model plain baselines |
| transfer/compA_v4_sonnet_cal, transfer/compA_v4_opus_cal | Sonnet / Opus 5.5 | compA_v4 harness, 2 constants refit on search fold 0 (300) | same harness, bigger model |

cafe2: Haiku candidates + Sonnet/Opus b2 only (cost).
Reference (not re-run): Nutrition5k paper Table 3 (2D direct 26.1%, trained on this data; different, uncleaned test split).
