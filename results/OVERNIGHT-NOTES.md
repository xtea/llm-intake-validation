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
