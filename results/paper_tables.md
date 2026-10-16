## TEST

**Nutrition5k test (cleaned, overhead)** (378 dishes)

| Model | System | MAE % [95% CI] | MPE % | MAE kcal | r | vs Haiku A, pts [95% CI] |
|---|---|---|---|---|---|---|
| Haiku 5.5 | Direct | 42.4 [37.2, 48.0] | +46.3 | 121 | 0.833 | +15.3 [+9.7, +21.3] |
| Haiku 5.5 | Plate-as-ruler | 32.6 [28.8, 36.6] | +13.6 | 93 | 0.819 | +5.5 [+2.5, +8.8] |
| **Haiku 5.5** | **Harness A** | **27.1 [24.3, 30.1]** | +3.8 | 77 | 0.874 | — |
| Sonnet 5.5 | Direct | 33.4 [28.9, 38.4] | +23.4 | 95 | 0.835 | +6.3 [+1.6, +11.2] |
| Sonnet 5.5 | Plate-as-ruler | 29.4 [26.2, 33.1] | -0.7 | 84 | 0.841 | +2.3 [-0.3, +4.9] |
| Sonnet 5.5 | Harness A | 28.9 [26.2, 31.8] | +6.3 | 82 | 0.862 | +1.8 [-0.2, +3.8] |
| Opus 5.5 | Direct | 34.5 [29.6, 40.4] | +31.8 | 98 | 0.846 | +7.4 [+2.1, +13.2] |
| Opus 5.5 | Plate-as-ruler | 28.8 [25.3, 32.8] | +15.7 | 82 | 0.857 | +1.7 [-1.7, +5.4] |
| Opus 5.5 | Harness A | 27.3 [24.5, 30.4] | +4.3 | 78 | 0.869 | +0.2 [-2.0, +2.3] |
| gpt-6-luna | Direct | 35.8 [31.9, 40.2] | +27.6 | 102 | 0.853 | +8.7 [+4.0, +14.0] |
| gpt-6-luna | Plate-as-ruler | 32.6 [29.2, 36.1] | +1.5 | 93 | 0.831 | +5.4 [+1.8, +9.3] |
| gpt-6-luna | Harness A | 26.4 [23.6, 29.2] | +0.1 | 75 | 0.882 | -0.8 [-3.0, +1.5] |
| gpt-6.1-sol | Direct | 48.5 [42.5, 55.5] | +63.3 | 138 | 0.852 | +21.4 [+14.2, +29.4] |
| gpt-6.1-sol | Plate-as-ruler | 34.6 [29.9, 40.0] | +29.5 | 99 | 0.836 | +7.4 [+2.4, +13.0] |
| gpt-6.1-sol | Harness A | 24.7 [22.2, 27.5] | -0.1 | 70 | 0.887 | -2.4 [-4.6, -0.3] |
| gpt-6-astra | Direct | 49.8 [43.5, 57.3] | +67.1 | 142 | 0.867 | +22.6 [+15.1, +31.0] |
| gpt-6-astra | Plate-as-ruler | 35.8 [31.1, 41.3] | +30.7 | 102 | 0.856 | +8.7 [+3.5, +14.2] |
| gpt-6-astra | Harness A | 25.0 [22.4, 27.9] | +1.3 | 71 | 0.890 | -2.1 [-4.2, -0.0] |

## CAFE2

**Nutrition5k cafe2** (221 dishes)

| Model | System | MAE % [95% CI] | MPE % | MAE kcal | r | vs Haiku A, pts [95% CI] |
|---|---|---|---|---|---|---|
| Haiku 5.5 | Direct | 53.8 [45.9, 63.8] | +72.9 | 140 | 0.626 | +16.4 [+9.8, +24.0] |
| Haiku 5.5 | Plate-as-ruler | 44.0 [38.4, 50.4] | +41.4 | 114 | 0.569 | +6.6 [+3.1, +10.3] |
| **Haiku 5.5** | **Harness A** | **37.4 [33.3, 41.8]** | +29.0 | 97 | 0.627 | — |
| Sonnet 5.5 | Plate-as-ruler | 39.8 [34.5, 46.4] | +38.4 | 104 | 0.641 | +2.4 [-1.4, +6.6] |
| Opus 5.5 | Plate-as-ruler | 46.1 [39.4, 54.7] | +58.9 | 120 | 0.681 | +8.7 [+2.7, +15.3] |
| gpt-6-luna | Direct | 64.5 [55.4, 75.4] | +85.2 | 168 | 0.676 | +27.1 [+18.1, +36.8] |
| gpt-6-luna | Plate-as-ruler | 49.8 [43.3, 57.9] | +50.0 | 130 | 0.608 | +12.4 [+6.2, +19.0] |
| gpt-6-luna | Harness A | 39.0 [34.4, 44.7] | +41.8 | 101 | 0.674 | +1.6 [-1.9, +5.4] |
| gpt-6.1-sol | Direct | 76.4 [65.3, 89.7] | +113.5 | 199 | 0.706 | +39.0 [+28.1, +50.7] |
| gpt-6.1-sol | Plate-as-ruler | 58.1 [49.3, 68.8] | +76.3 | 151 | 0.686 | +20.6 [+12.7, +29.7] |
| gpt-6.1-sol | Harness A | 34.2 [29.6, 40.0] | +35.0 | 89 | 0.715 | -3.2 [-6.8, +0.9] |
| gpt-6-astra | Direct | 78.6 [67.3, 92.3] | +118.2 | 204 | 0.705 | +41.2 [+30.6, +53.4] |
| gpt-6-astra | Plate-as-ruler | 57.0 [48.2, 67.2] | +74.4 | 148 | 0.713 | +19.6 [+11.3, +28.6] |
| gpt-6-astra | Harness A | 35.0 [30.5, 40.6] | +37.2 | 91 | 0.728 | -2.4 [-6.0, +1.5] |

## NVREAL

**NutritionVerse-Real** (224 dishes)

| Model | System | MAE % [95% CI] | MPE % | MAE kcal | r | vs Haiku A, pts [95% CI] |
|---|---|---|---|---|---|---|
| Haiku 5.5 | Direct | 50.4 [44.7, 55.7] | -4.1 | 438 | 0.701 | -5.2 [-7.6, -2.8] |
| Haiku 5.5 | Plate-as-ruler | 50.7 [45.3, 56.0] | -18.0 | 441 | 0.735 | -4.9 [-6.4, -3.3] |
| **Haiku 5.5** | **Harness A** | **55.6 [50.5, 60.4]** | -28.3 | 484 | 0.749 | — |
| Sonnet 5.5 | Plate-as-ruler | 50.7 [45.5, 55.7] | -24.3 | 441 | 0.781 | -4.9 [-6.7, -2.8] |
| Sonnet 5.5 | Harness A | 57.3 [52.5, 61.8] | -31.8 | 499 | 0.777 | +1.7 [+0.7, +2.9] |
| Opus 5.5 | Plate-as-ruler | 44.9 [39.6, 50.3] | -12.1 | 391 | 0.803 | -10.6 [-12.6, -8.6] |
| Opus 5.5 | Harness A | 50.4 [45.2, 55.4] | -24.5 | 439 | 0.804 | -5.2 [-6.4, -3.9] |
| gpt-6-luna | Direct | 48.3 [43.2, 53.4] | -6.2 | 420 | 0.739 | -7.3 [-9.2, -5.1] |
| gpt-6-luna | Plate-as-ruler | 48.9 [43.7, 54.0] | -15.4 | 425 | 0.754 | -6.7 [-8.8, -4.5] |
| gpt-6-luna | Harness A | 53.1 [48.1, 57.9] | -23.6 | 462 | 0.762 | -2.4 [-3.6, -1.2] |
| gpt-6.1-sol | Direct | 43.9 [38.6, 49.3] | +0.3 | 382 | 0.808 | -11.7 [-14.0, -9.1] |
| gpt-6.1-sol | Plate-as-ruler | 42.6 [37.4, 48.0] | +2.1 | 371 | 0.807 | -12.9 [-15.6, -10.1] |
| gpt-6.1-sol | Harness A | 51.5 [46.6, 56.5] | -27.6 | 449 | 0.815 | -4.0 [-5.4, -2.6] |
| gpt-6-astra | Direct | 43.3 [38.1, 48.6] | +1.9 | 377 | 0.814 | -12.3 [-14.7, -9.6] |
| gpt-6-astra | Plate-as-ruler | 42.3 [37.2, 47.6] | +4.3 | 368 | 0.816 | -13.3 [-16.0, -10.4] |
| gpt-6-astra | Harness A | 51.1 [46.1, 56.0] | -27.2 | 444 | 0.826 | -4.5 [-5.8, -3.1] |

## SIDE

**Same protocol** (676 dishes)

| Model | System | MAE % [95% CI] | MPE % | MAE kcal | r | vs Haiku A, pts [95% CI] |
|---|---|---|---|---|---|---|
| Haiku 5.5 | Direct | 56.9 [48.1, 66.7] | +107.3 | 144 | 0.856 | +18.5 [+12.8, +25.4] |
| Haiku 5.5 | Plate-as-ruler | 43.2 [34.5, 54.6] | +48.7 | 109 | 0.870 | +4.8 [+2.7, +7.4] |
| **Haiku 5.5** | **Harness A** | **38.5 [29.3, 51.1]** | +47.8 | 97 | 0.895 | — |
| Sonnet 5.5 | Plate-as-ruler | 40.4 [31.5, 52.6] | +21.5 | 102 | 0.890 | +2.0 [+0.0, +4.0] |
| Opus 5.5 | Plate-as-ruler | 43.8 [34.5, 55.8] | +56.2 | 110 | 0.885 | +5.4 [+2.7, +8.8] |
| gpt-6-luna | Harness A | 43.0 [34.0, 55.3] | +78.2 | 108 | 0.868 | +4.6 [+2.2, +7.7] |
| gpt-6.1-sol | Plate-as-ruler | 56.1 [46.8, 66.4] | +90.4 | 141 | 0.870 | +17.6 [+11.8, +24.9] |
| gpt-6.1-sol | Harness A | 40.2 [30.8, 52.7] | +51.1 | 101 | 0.885 | +1.7 [-0.5, +4.4] |

## ABLATION

| Model | Split | Direct | Direct + cal | Plate | Plate + cal | A without cal | A |
|---|---|---|---|---|---|---|---|
| Haiku 5.5 | test | 42.4 | 29.5 | 32.6 | 31.0 | 27.0 | 27.1 |
| Haiku 5.5 | cafe2 | 53.8 | 35.2 | 44.0 | 39.1 | 40.2 | 37.4 |
| Haiku 5.5 | nvreal | 50.4 | 58.7 | 50.7 | 57.8 | 51.8 | 55.6 |
| Sonnet 5.5 | test | 33.4 | 31.0 | 29.4 | 29.4 | 28.6 | 28.9 |
| Sonnet 5.5 | cafe2 | – | – | 39.8 | 37.7 | – | – |
| Sonnet 5.5 | nvreal | – | – | 50.2 | 54.7 | 53.2 | 57.3 |
| Opus 5.5 | test | 34.5 | 28.8 | 28.8 | 27.6 | 26.8 | 27.3 |
| Opus 5.5 | cafe2 | – | – | 46.1 | 37.1 | – | – |
| Opus 5.5 | nvreal | – | – | 44.9 | 51.0 | 44.8 | 50.4 |
| gpt-6-luna | test | 35.8 | 27.9 | 32.6 | 29.4 | 27.2 | 26.4 |
| gpt-6-luna | cafe2 | 64.5 | 39.5 | 49.8 | 39.4 | 43.4 | 39.0 |
| gpt-6-luna | nvreal | 48.3 | 57.0 | 48.4 | 57.4 | 49.1 | 53.1 |
| gpt-6.1-sol | test | 48.5 | 26.4 | 34.6 | 28.5 | 30.0 | 24.7 |
| gpt-6.1-sol | cafe2 | 76.4 | 36.1 | 58.1 | 36.3 | 54.3 | 34.2 |
| gpt-6.1-sol | nvreal | 43.9 | 54.8 | 42.6 | 50.3 | 43.8 | 51.5 |
| gpt-6-astra | test | 49.8 | 26.1 | 35.8 | 28.6 | 31.9 | 25.0 |
| gpt-6-astra | cafe2 | 78.6 | 35.9 | 57.0 | 33.6 | 56.8 | 35.0 |
| gpt-6-astra | nvreal | 43.3 | 55.2 | 42.3 | 51.6 | 42.2 | 51.1 |

## CONFIG

| Model | API id | System | Calls/dish | Effort | Fitted constants (data) |
|---|---|---|---|---|---|
| Haiku 5.5 | `claude-haiku-5-5` | Direct | 1 | low | — |
| Haiku 5.5 | `claude-haiku-5-5` | Plate-as-ruler | 1 | medium | — |
| Haiku 5.5 | `claude-haiku-5-5` | Harness A | 6 | low/medium | C=−0.074, W=0.930 (search) |
| Haiku 5.5 | `claude-haiku-5-5` | Harness A-v2 | 6 | low/medium | 6 constants (search) |
| Haiku 5.5 | `claude-haiku-5-5` | Harness B | 3 | low/medium | none |
| Haiku 5.5 | `claude-haiku-5-5` | Harness C | 2 | low/medium | C=−0.120, two weights (search) |
| Sonnet 5.5 | `claude-sonnet-5-5` | Harness A | 6 | low/medium | C=−0.04, W=0.87 (fold 0) |
| Opus 5.5 | `claude-opus-5-5` | Harness A | 6 | low/medium | C=−0.12, W=0.945 (fold 0) |
| GPT-6 luna | `gpt-6-luna` | Harness A | 6 | low/medium | C=−0.035, W=0.855 (fold 0) |
| GPT-6.1 sol | `gpt-6.1-sol` | Harness A | 6 | low/medium | C=−0.27, W=1.02 (fold 0) |
| GPT-6 astra | `gpt-6-astra` | Harness A | 6 | low/medium | C=−0.27, W=0.99 (fold 0) |

Images: PNG, long side ≤1024 px (Nutrition5k overhead images are 640×480). Claude: Messages API, adaptive thinking with the stated effort, no temperature setting. GPT: chat completions, image as data URL with detail=high, reasoning_effort mapped from the stated effort. Prompts are byte-identical across models. Full prompts and code are in the repository.

## FAILURES

| Split | System | Parse failures | Network failures (retried) |
|---|---|---|---|
| nvreal | b2_plate_scale | 1 | 0 |
| nvreal | b2_plate_scale_gpt_6_luna | 2 | 0 |
| acetada | h2_plate_scale | 0 | 33 |
| n5k_side | compA_v4 | 1 | 0 |
| n5k_side | compA_v4_cal_gpt_6_1_sol | 1 | 0 |
| n5k_side | compA_v4_cal_gpt_6_luna | 1 | 0 |
| n5k_side | compB_v1 | 1 | 0 |
