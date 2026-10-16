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
- 2026-10-16 operational deviation (ACETADA): `h2_plate_scale` had 33 API timeouts (network, not parse failures) in its single run;
  only those calls were retried (successful calls served from cache; same prompts, same sample indices). The pre-retry file is kept
  as runs/h2_plate_scale/acetada-all.before-retry.json. All other ACETADA systems ran without network failures.

## Addendum F: view ablation of harness A (added 2026-10-16, before computing; exploratory; no new model calls)
Question (raised by our own ACETADA result): does harness A fail on ACETADA without calibration because of its dataset-tagged
views (P: direct view with cafeteria serving-size prior; DN: identification rules from Nutrition5k labels), or because of other
structural differences from B? Variants re-use A's cached calls, with calibration removed (C=0) and equal weights:
R only; DN only; P only; R+DN (no P); R+P (no DN); R+DN+P (= A-raw). Scored on test, nvreal, acetada.
Reading rule written in advance: if dropping P (and/or DN) brings A-raw close to the plain prompts on acetada, the dataset-tagged
content explains the gap; if not, the gap is not explained by the tagged content.

## Addendum G (2026-10-16, POST HOC — written after computing; not pre-registered)
Day-level agreement on ACETADA for comparison with the trial's 24-hour recall report (Whitton et al., AJCN 2024).
Added after all other results were known, in response to a venue-fit review (CHIL criteria: clinical anchoring).
- Unit: participant feeding day = breakfast + lunch + dinner, only days with all three meals in the cleaned set (130 days, 94 participants).
- Statistics: mean of day % errors (participant bootstrap 95% CI, 2,000), Bland-Altman 95% LoA, share of days within 800 kJ.
- Local recalibration: 2 constants refit on k=20 meals from other participants; days of those participants excluded; 200 draws.
- Meal-level breakdown by meal slot (clock hour) and energy tertile on ACETADA and test.
- Offline from cached outputs; no model calls. Code: fe/clinical.py, fe/figures.py (fig_ba). Output: results/clinical.txt.
- Reported in the paper as post hoc and indicative (served vs consumed energy; selected days).

## Addendum H (2026-10-16) — Direction B: consumed intake from before + after photos. PRE-REGISTERED (written before any dual-image call)
Data: ACETADA, consumed energy and macros per meal (weighed). Labels: data/labels/acetada_intake.json (fe/intake.py build):
802 meals, 152 participants (806 rows − 2 duplicate photo rows [3057 2021-08-03 Dinner, 3088 2021-10-19 Dinner] − 1 meal <30 kcal − 1 no-food photo).
Before images = existing PNGs; after images = data/images_after/ (PNG, ≤1024 px).

Primary questions
- Q1. Does adding the after photo improve consumed-energy estimates vs the before photo alone (single image = existing direct prompt, i.e. assumes all eaten)?
  Metric: meal-level MAE% vs consumed energy, and signed bias; paired participant bootstrap CI of the difference. Pre-specified subgroup: meals with ≥10% of served energy left.
- Q2. Is the change (dual − single) consistent across model tiers? Models: Claude Haiku/Sonnet/Opus 5.5, GPT-6 luna / 6.1 sol / 6 astra. Report the difference per model with CI; "consistent" = same sign for all six.
- Q3. Summed over complete feeding days (breakfast+lunch+dinner), are mean bias and individual error small enough?
  Pre-set thresholds: |mean day % error| ≤ 10% (group level) and 95% Bland–Altman LoA within ±30% (individual level; the best recall method in the same trial, mFR-TA, reached about ±30%).
  Indirect reference only: published Table 3 of Whitton et al. 2024 (ASA24, Intake24, mFR-TA, IA-24HR). We will not claim superiority over recall methods.
Secondary: protein, carbohydrate and fat eaten (same metrics). Further optimization (calibration, agentic harness search, local recalibration) is a separate, exploratory section.

Prompts (frozen now): candidates/intake/dual_direct_{model}.py — one call, both images, asks served, left over, eaten kcal and eaten macros. effort=low.

Pilot (go/no-go; ~$10): 100 meals drawn with seed "pilot-B" from meals that have cached single-image runs; Haiku 5.5 and GPT-6.1 sol only.
- GO if, for GPT-6.1 sol, the dual-image bias vs consumed is closer to zero than single-image by ≥5 points AND the Spearman correlation between predicted and true eaten fraction is ≥0.3.
- If the prompt is changed after the pilot, the 100 pilot meals are excluded from all final analyses. If not changed, they stay in.
- NO-GO → fall back to direction A (no further dual-image runs).
Budget: pilot ≤ $15; full study ≤ $150 (dev keys), requires the pilot GO.
