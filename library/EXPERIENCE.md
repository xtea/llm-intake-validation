# Experience library (Harness²-style, harnessing-level memory)

Each lesson: tag = [invariant] (general estimation reasoning, should transfer to any photos),
[domain] (food knowledge, should transfer across food datasets), [dataset] (fitted to / specific to
Nutrition5k: fixed overhead camera, Google cafeteria plates — expected NOT to transfer).
Evidence = search-300 unless noted. All numbers are mae_pct_of_mean (lower is better). Haiku 5.5 only.

## Gen 1 (2026-10-15), base h2_plate_scale = 37.65

### Portion / geometry
- [invariant] Plate-as-ruler prompt (dinner plate ~26 cm, bowl ~15 cm; footprint × height) is the strongest single-call
  baseline: 48.5 (direct) → 37.7. Sonnet: 34.4 → 30.9. Evidence: h0 vs h2, b0 vs b2.
- [invariant] Written step-by-step procedure in the answer (vessel area → per-item coverage % that must sum to the
  covered area → bulk volume → apply ONE packing/density factor → kcal) beats JSON-only + code arithmetic
  (33.8 vs 38.3, rsn_v6 vs rsn_v7). Failure fixed: the model multiplied void factor and density twice; and it guessed a
  total first then rationalized it.
- [invariant] Averaging independent mass estimates from different procedures reduces variance (corr of mass errors
  0.5–0.65): geo_v5 32.2. Averaging the SAME prompt (h3, rsn chains) helps only if the base prompt is good.
- [dataset] Fixed frame-width constant (45 cm) beats the model's plate size (model says 26 cm for ~90% of plates).
  Works only because the Nutrition5k camera is fixed. geo_v5.
- [invariant] Per-piece weights from the model run 15–30% high (typical-serving pull). geo.
- [invariant] Range answers (low/likely/high) do not help (36.35 vs 36.43). rsn.
- [invariant] effort high is worse than medium on Haiku 5.5 (38.0 vs 37.7; 35.5 vs 34.2); low ≈ medium and cheaper. rsn.

### Composition / density
- [domain] Common misidentifications cause the largest density errors: egg whites read as feta (5×), olives as dates,
  sweet potato as cheese. Naming them + giving as-served kcal/100 g reference values helped: 37.7 → 34.9 (den_v3).
- [domain] Do not assume hidden fat everywhere (den_v1 raised bias). Cooked vegetables 25–50 kcal/100 g without oil.
- [dataset] Leafy-green salads: 85% dressed in search labels, oil ≈ 11% of greens' weight → code adds oil at 9% of
  flagged raw greens (den_v4). Fitted from training labels; cafeteria-specific.
- [invariant] A second pass that re-scores density on the same image did not help (den_v2).

### Aggregation / calibration
- [invariant] Estimates are too spread out, not just biased: log-log slope of truth on estimate ≈ 0.72–0.76 for every
  prompt. A sub-linear post-hoc map kcal = 300·exp(C + w·ln(x/300)) is the single biggest MAE gain (cal_v1: 2 constants
  on h2 → 33.3 on 300, 34.7 on unseen dishes).
- [dataset] Global scale factors 0.82–0.88 and fitted exponents are dataset calibration.
- [invariant] Combining low-correlation views helps (h0 vs plate-scale direct prompt corr 0.81); combining
  high-correlation prompts (h0/h1/h2, 0.82–0.88) does not; self-critique of an item list is ~identical to the original
  (corr 0.96). ens.
- [dataset] Prompt text "cafeteria serving, small 100–300 kcal, full plate 700–1000 kcal" (ens_v5) — dataset prior.
- [caution] Shrinkage lowers MAE but WORSENS small/large tercile bias (any MAE-optimal shrinkage does). cal.

### Ceiling observed
- mass_slope stays 0.72–0.88 across all five directions: gen1 removed bias and variance, not portion discrimination.
- Overfitting check (cal): cal_v7 30.5 on search-300 vs 34.4 on 321 unseen search dishes (h2 on those: ~38).
  search-300 has been used ~40× for selection → use full search or a fresh seed for gen2 fitness.

## Gen 1 select-split results (784 held-out dishes; never used for tuning)
See `python3 -m fe.board select-all`. h2 38.35 · cal_v7 31.52 · ens_v11 32.34 · geo_v5 32.89 · den_v7 34.87 · den_v5 37.39.
- calibration/ensembling: lowest MAE via shrinkage (slope 0.70–0.77, small bias ~+50%).
- geometry (geo_v5): best discrimination (slope 0.87) and bias (+4.5%).
- density rules (den_v5) mostly overfit search-300 (34.2 → 37.4 on select).

## Gen 2 (2026-10-15/16) — Harness²-style composition; fitness = fresh search seeds g2/g2b (600)
Select (784, scored once per finalist): compA_v2 29.5 · compA_v4 29.8 · compC_v5 31.1 (2 calls, slope 0.93) ·
compB_v1 31.8 (no fitted constants, bias +3.7) · compB_v3 31.9 · disc_v7 34.6 (slope 0.92). gen1 best was 31.5; h2 38.4.
- [invariant] Per-view stacking weights do not transfer between subsets; equal-weight geometric mean + 2-constant power law
  is more robust (compA). Disagreement-driven shrinkage overfits.
- [invariant] The partner worth adding is the one with least-correlated error: density-rules view (r=0.50 with rsn) >
  prior view (0.65) >> geometry views (0.87, add nothing). A second call pays only if it is a different procedure
  (0.63 → −2 pts; same prompt resampled 0.93 → ~0).
- [invariant] Per dollar, calibration beats reasoning: cheapest direct call + 2 constants ≈ rsn_v6 chain + 2 constants (6× cost).
- [CORRECTED gen3/F] Density (kcal/g) error is as large as mass error (log sd ≈ 0.45 vs 0.42). The "r = 0.93" was SAME-prompt
  resampling; ACROSS views density errors correlate 0.64–0.76. Much of the shared part is dataset labelling convention
  (egg whites +0.53, Caesar salad +0.68, dressing counted in raw greens −0.3…−0.6): these alone = 29% of shared squared
  density error over 980 dishes.
- [dataset] RETAG den_v3/den_v7 rules ([domain] → [dataset]): their gains are egg-white-vs-feta and dressed/sautéed greens
  specific to this cafeteria; generic look-alike phrasing does not reproduce them (compB).
- [CORRECTED gen3/G] Household-unit counting (tsp/tbsp/ping-pong ball/deck of cards/cup, or pieces × one piece) raises mass_slope
  0.81 → 0.915, BUT slope = r × (sd_est/sd_true): disc_v6 is r=0.846 × 1.08 over-dispersion; compA's mass r is HIGHER (0.894).
  Within-plate slope ≈ 1.0 holds for every view, not only counting. Use r (log-mass correlation) as the discrimination
  metric. Honest summary: evolution removed bias and some variance; discrimination (r) barely moved. Remaining compression is BETWEEN dishes
  (vessel size: Haiku calls ~90% of plates 26 cm; hidden layers). Heights written by the model are ~constant (r≈0.03 with
  true mass). Slope and MAE trade off: counting reads ~20% heavy and noisier (disc).
- [invariant] Sonnet 5.5 reaches slope 0.94 with a plain prompt on the same dishes (disc) → scale judgment is partly capability.

## Gen 3 (2026-10-16) — plateau. No candidate beats compA_v4 significantly on truly fresh dishes.
- E (add counting/geo views to compA): ties compA at 75% cost (E_v3) — drop the 2nd reasoning chain (r=0.96 with the 1st);
  but P (prior) resampling ×3 is worth 0.45 on fresh dishes.
- F (decorrelate density: blind description → text-only density, probabilistic identity, Atwater from macros): standalone
  35.3, no ensemble gain. Short single-call views give the best densities (DN 0.29, P 0.36 log sd); long itemised chains
  the worst (0.44). Even perfect density would leave the ~0.36 mass error → density alone cannot reach 26.1.
- G (vessel type/depth, bowls = fill × capacity): G_v5 30.71 vs compA 31.39 on fresh, CI [−1.42, +0.05]. Asking Haiku for
  vessel size does not correlate with its error; between-dish "compression" is noise, not scale bias.
- H (1,404 view subsets, robust combiners, item-level merging, guards): mean beats every robust combiner (errors are shared
  bias, not outliers); item-level merge worse than totals; only guard that matters is all-views-fail fallback.
- [invariant][method] Choosing compositions by CV on one 600-dish sample does not transfer, even with paired CIs excluding 0:
  earlier seeds overlapped (only ~130–314 dishes were never used). FIX applied: search now has 3 disjoint plate-grouped
  folds (`--fold 0/1/2`), each to be used once per decision; image-only no-food scan removed 4 search images
  (data/exclude_nofood.json; select/test/cafe2 had none).
- Residual error is 57–80% plate-level and shared across views (r 0.72–0.78): another single-image Haiku prompt will not
  reach 26.1. Next lever is the model (harness transfer to Sonnet 5.5), not the harness.
