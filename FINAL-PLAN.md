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

## Out-of-distribution split `nvreal` (added 2026-10-16, before any run on it)
NutritionVerse-Real (Univ. of Waterloo; Kaggle nutritionverse/nutritionverse-real; CC BY-NC-SA 4.0, academic use only,
images not redistributed). iPhone 13 Pro Max photos, per-item weighed, Canadian Nutrient File. One image per dish (first
file name in sorted order), dishes with ≥30 kcal: 224 dishes; median 586 kcal / 350 g (Nutrition5k median ≈ 250 kcal).
Images converted to PNG, long side ≤1024 px, random ids. Sealed (`--final`), each candidate run once.
Candidates: all Haiku candidates of the test table + sonnet/b2_plate_scale + opus/b2_plate_scale_opus +
transfer/compA_v4_sonnet_cal + transfer/compA_v4_opus_cal. Fitted constants are NOT refit on nvreal.
Hypothesis stated in advance: candidates with dataset-fitted shrinkage toward ~300 kcal (compA_v2/v4, compC_v5) will lose
part of their advantage on larger meals; the zero-constant harness (compB_v1) should transfer best.

## Execution log and deviations (2026-10-16)
- All pre-registered runs completed. Two operational deviations: (1) `transfer/compA_v4_opus_cal` on nvreal stopped at the
  $20 per-run safety cap after partial completion and was RESUMED (cached calls reused, remaining calls made) — not re-run
  or changed; (2) `sonnet/b2_plate_scale` on nvreal had 1 parse failure, scored as the worst error per evaluator rules.
- Post-hoc (NOT pre-registered) sensitivity analysis on nvreal: every NutritionVerse-Real food type carries one constant
  weight across all dishes (42/42 types), i.e. each physical item was weighed once and re-plated; "meatloaf" (701 g per
  piece, 14 dishes) is visually implausible for the slices in the photos. Excluding those 14 dishes lowers all errors by
  ~5–7 points but does not change the ranking or any conclusion.
- Pre-registered decision rule 3 outcome: scenario C (no evolved system beats the plain baseline on nvreal). The predicted
  direction held: dataset-fitted shrinkage (compA_v4, compC_v5) degrades most; the zero-constant harness (compB_v1) ties the
  plain prompt.
