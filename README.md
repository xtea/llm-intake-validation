# food-evolve

Agentic evolutionary search for food-energy estimation pipelines from meal photos,
scored against weighed ground truth (Nutrition5k overhead RGB, CC BY 4.0).

Private until publication. Pure academic research code.

## Layout
- `fe/data.py` — builds plate-grouped, label-cleaned splits: search / select (from official depth_train),
  sealed test (official depth_test minus cross-split re-scans), sealed cafe2 holdout. Images renamed to random ids.
- `fe/llm.py` — cached, cost-counted Claude client (only Haiku 5.5 / Sonnet 5.5 / Opus 5.5 allowed).
- `fe/evaluate.py` — scores a candidate `estimate(image_bytes, llm) -> {"kcal", "mass_g"}`; static checks block
  file access, non-stdlib imports and embedded lookup tables. Sealed splits need `--final` and are logged.
- `fe/board.py` — leaderboard.
- `candidates/` — pipelines. `h*` = Haiku 5.5 baselines, `sonnet/` = Sonnet 5.5 baselines, `gen*/` = evolved.

## Protocol
1. Evolve on `search` (fixed 300-dish subset for speed; full search for promotion).
2. Choose finalists on `select` only.
3. Run `test` and `cafe2` once, at the end, with `--final`.
