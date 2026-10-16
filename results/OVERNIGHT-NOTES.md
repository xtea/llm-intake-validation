# Overnight 2026-10-16 (Jason: 今晚不停跑,额外预算 $200,目标=有价值的论文)
Spend baseline at start: $333.22 (runs/*/ logged usd). Tonight's experiments = addenda B, C, D (+ACETADA if downloaded).

## Key findings so far
1. GPT-6 family (test): the Haiku-evolved harness A transfers to GPT and gives the best test numbers so far:
   gpt-6.1-sol A 24.7%, astra 25.0%, luna 26.4% (direct: 48.5 / 49.8 / 35.8). Plain GPT over-estimates (+63–67% MPE).
2. Calibration ablation (results/ablation-*.txt): on test, direct prompt + 2 constants fitted on fold 0 gets within 0–2.4 pts
   of A (Haiku: b0+cal 29.5 vs A 27.1, Δ +2.4 [0.6,4.2]; GPT-sol 26.4 vs 24.7; astra 26.1 vs 25.0; Opus b2+cal 27.6 vs 27.3).
   Haiku A-raw (no calibration) 27.0 ≈ A on test. On nvreal, source-fitted calibration HURTS every system by 4–9 pts;
   removing A's calibration recovers ~4 pts (Haiku 55.6 → 51.8) to baseline level (50.4–50.7).
   → Paper reframe: most benchmark gain = calibration absorbing the dataset prior; evolved structure adds 0–2.4 pts;
     calibration is what fails OOD; structure neither helps nor clearly hurts OOD.
3. Target recalibration (results/recal-nvreal.txt): k=10 hurts (overfit); k=20–50 recovers 2–5 pts; nvreal stays 43–49%
   for every method → OOD error is mostly noise/discrimination, not bias. GPT-sol plain prompt best on nvreal (42.6%).
## Pending
- n5k_side same-protocol (addendum C), GPT nvreal for sol/astra harness, repeats on test, ACETADA (2nd OOD) download.
4. GPT-6 full (test/cafe2/nvreal) done. nvreal: GPT-sol b0 43.9, b2 42.6, A 51.5, A-raw 43.8; astra b0 43.3, b2 42.3, A 51.1,
   A-raw 42.2. Same pattern for all 6 models: source-fitted calibration hurts OOD (GPT-large by 8–9 pts); A-raw ≈ plain prompts.
   cafe2: GPT A sol 34.2 / astra 35.0 best; plain GPT over-estimates massively (+113–118% MPE b0).
5. Repeat calls on test (fresh samples ×2): compA_v4 27.1/26.4/26.2; h2 32.6/33.9/33.0; Sonnet b2 29.4/29.6/29.8 → ≤1.3 pts.
6. Opus A-raw on cafe2 not run (not cached; Opus A was never run on cafe2 by design).
7. 22:28 local: an unknown detached script `scratchpad/resume_all.sh` (not started from this conversation's visible turns) was
   re-running the same addenda C/E/repeat jobs in parallel (max-usd 60). It duplicated running work (double spend, racing writes).
   Stopped at ~23:35 (PIDs 33552/45603); no unique work lost (all completed calls cached).
8. Same-protocol (n5k_side, uncleaned rgb_test, one side frame): Haiku A 38.9, B 39.8, h2 43.2, h0 56.9, Sonnet b2 48.8 (6 infra
   failures, retry pending), Opus b2 43.8 → far from the trained 2D model's 26.1%.
9. ACETADA interim: Haiku h0 24.8% (MPE −15.6); h2 29.9 with 33 infra failures (retry pending).
10. ACETADA final (766 meals): plain prompts 17.4–25.3% (Opus plate best); A 40.0, A-v2 38.3, C 51.7, B 26.7; GPT-sol A 32.5.
    Source calibration hurts by 7–21 pts. A-raw 33.2 still worse than plain.
11. Addendum F view ablation (cached, $0): on ACETADA the worst view is R (written reasoning, tagged INVARIANT) 39.0%; DN (tagged
    dataset) 26.2%; dropping P does not help (33.5). R's prompt assumes an overhead photo + standard plate diameters → hidden
    dataset assumption inside an "invariant" component. Tags are NOT a reliable predictor; paper says so.
12. Merged into the other session's fuller v0.3 (doc/credit/drafts/paper4-v03.md); PDF 14–15 pp, arXiv source compiles.
13. Spend (per-call cache records): whole project $573; since 20:50 CDT $242 (includes the approved GPT-full tail and the duplicate
    session's runs) → overnight $200 exceeded by ~$40.
