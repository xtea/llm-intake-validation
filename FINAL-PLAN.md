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
- Decision rule 3 (stated in chat after the runs started, before any sealed result was read; NOT in the committed plan) outcome: scenario C (no evolved system beats the plain baseline on nvreal). The predicted
  direction held: dataset-fitted shrinkage (compA_v4, compC_v5) degrades most; the zero-constant harness (compB_v1) ties the
  plain prompt.

## Addendum A: OpenAI GPT-6 family (added 2026-10-16, before any GPT run on test/cafe2/nvreal)
Models (developers.openai.com pricing, 2026-10-16): gpt-6-luna (small, $0.10/$0.50), gpt-6.1-sol (mid, $2/$10),
gpt-6-astra (large, $10/$50). Same systems as for Claude: direct prompt (b0), plate-as-ruler prompt (b2), and the Haiku-evolved
harness A (compA_v4 structure) with its 2 calibration constants refit on the same 300 dishes of search fold 0 used for
Sonnet/Opus. Prompts are byte-identical to the Claude versions; only the model id changes (OpenAI chat completions,
image as data URL with detail=high; our effort levels map to reasoning_effort low/medium/high).
Splits: test, cafe2, nvreal; each system run once per split. If budget is limited, gpt-6-astra harness A runs on test and
nvreal only (decided before any result; will be stated). Same metric, same bootstrap, same decision rules as for Claude.
Question added in advance: does a harness evolved for one vendor's small model transfer to another vendor's models?
Decision 2026-10-16 (before any GPT result on sealed splits): full design — all three GPT models, all systems, all three
sealed splits (Jason: "完整版").

## Addendum B: post-review exploratory analyses (added 2026-10-16, after an external review; NOT pre-registered)
Requested by a methodological review of v0.2. All results below are labelled exploratory in the paper.
1. Calibration ablation. For every model, fit the same 2-constant power law (kcal = 300·exp(C + W·ln(x/300)), grid as before,
   minimise Σ|err| / Σ truth) on search fold 0 (the same 300 dishes used for the cross-model refit) for: direct prompt (b0),
   plate-as-ruler prompt (b2). Apply the fitted constants unchanged to test, cafe2, nvreal outputs. Also score harness A with its
   calibration removed (C=0, W=1; same model calls). Compare: b0, b0+cal, b2, b2+cal, A-raw, A.
2. Repeated calls: Haiku A, Haiku b2 (h2) and Sonnet b2 re-run twice on test with new sample indices (fresh model calls) to
   measure call-to-call variation.
3. Metrics reported with explicit formulas: MAE% = Σ|ŷ−y| / Σy; MPE = mean((ŷ−y)/y); MAE in kcal.
No harness, prompt or constant of the original systems is changed; no new tuning on sealed splits.

## Addendum C: same-protocol comparison with the Nutrition5k paper (added 2026-10-16 before any run; exploratory)
Split `n5k_side`: the official `rgb_test_ids` (709 dishes) with NO cleaning, as in the original paper (re-scans, sub-30 kcal and
saturated labels kept; cafe2 totals recomputed from item rows). Input: ONE frame per dish, the first decodable frame of side-angle
camera A (fallback B, C, D), PNG, long side ≤1024 px. The paper's 2D model used every 5th frame of the side videos; ours sees one
frame, zero-shot. Metric MAE% of mean (their Table 3 convention). Systems (run once): Haiku h0, Haiku h2, Haiku A (compA_v4),
Haiku B (compB_v1), Sonnet b2, Opus b2, gpt-6-luna A (cal), gpt-6.1-sol b2, gpt-6.1-sol A (cal). No constants refit; the harness
prompts say "overhead photo" and are not edited (a mismatch we report). Reference: 26.1% (Thames et al. 2021, Table 3).

## Addendum D: target-domain recalibration (added 2026-10-16, before computing; exploratory, offline, no new model calls)
On nvreal, for each model and for b0, b2 and A-raw outputs: draw k labelled dishes (k = 10, 20, 50) at random, fit the same 2-constant
power law on them, score MAE% on the remaining dishes; 200 random draws per k; report mean and 5–95% range. Question: how many target
labels does it take to recover from the source-domain calibration failure, and does A's structure help once calibration is local?

## Addendum E: second out-of-distribution set ACETADA (added 2026-10-16, before any run; exploratory)
ACETADA (Coburn et al., BHI 2025; CC BY-NC 4.0, non-commercial research; images not redistributed): controlled feeding trial,
Perth, Western Australia; 806 meals with a before-eating photo; each item weighed before and after. Truth = energy SERVED on the
plate in the before photo: per item, density = energy_kcal / consumed_g, served kcal = density × before_portion_g. Meals where any
item has before_portion_g > 0 but consumed_g = 0 (density unknown) are excluded; ≥30 kcal inclusion as before. Image: before photo,
converted to PNG (EXIF incl. GPS/time removed), long side ≤1024. Grouping for bootstrap: participant_id.
Systems (run once; budget-limited, chosen before results): Haiku h0, h2, A (compA_v4), A-v2, B, C; Sonnet b2; Opus b2;
gpt-6-luna b0, b2, A; gpt-6.1-sol b0, b2, A; gpt-6-astra b2. Same metric/bootstrap; same calibration-ablation recipe (fold-0 fits).
Prediction stated in advance (from the tags and the nvreal result): systems with source-fitted calibration lose more than their
uncalibrated counterparts; serving sizes in a feeding trial are closer to Nutrition5k than nvreal, so the loss may be smaller.

## Execution log, addenda C/E (2026-10-16)
- Infrastructure errors (APITimeoutError / APIConnectionError, from running many jobs in parallel) are not model behaviour.
  Rule applied to ALL systems on n5k_side and acetada: after the batch finishes, re-run each
  system once; successful calls come from cache (unchanged), only infrastructure-failed items are retried. Honest note: the rule
  was written after interim scores of 8 systems had been seen; it is applied uniformly to every system. Model-output parse
  failures are kept and scored as before.
