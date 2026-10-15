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
