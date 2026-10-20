<<MODELS>>
Haiku 5.5, Sonnet 5.5, Opus 5.5, GPT-6 luna, GPT-6.1 sol, GPT-6 astra, Gemini 3.8 Flash, Gemini 4 Argon

<<TABLE2>>
| Model | Before only | Before × c | Subtraction | Both photos | Both photos, valid subset (n) | Δ vs before only | Δ vs before × c | Δ vs before × c, ≥10% left |
|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | 24.7 (−6.7) | 27.3 | 36.5 (−33.5) | 24.9 (−14.0) | 24.1 (800) | +0.1 [−1.9, +2.3] | −2.5 [−4.2, −0.6] | −1.8 [−4.4, +0.6] |
| Sonnet 5.5 | 24.2 (+0.9) | 24.9 | 25.1 (−18.4) | 21.8 (−2.9) | 19.3 (789) | −2.4 [−5.3, +0.2] | −3.0 [−5.5, −0.8] | −1.3 [−5.9, +2.7] |
| Opus 5.5 | 30.1 (+21.7) | 22.7 | 21.2 (+1.8) | 20.5 (+9.0) | 20.5 (801) | −9.6 [−13.2, −6.5] | −2.2 [−4.8, +0.3] | −7.5 [−12.3, −3.3] |
| GPT-6 luna | 23.9 (+4.3) | 23.7 | 26.2 (−17.6) | 21.0 (−6.1) | 21.0 (802) | −2.8 [−5.0, −1.0] | −2.6 [−4.2, −1.1] | −1.3 [−5.1, +1.9] |
| GPT-6.1 sol | 26.9 (+14.8) | 22.3 | 23.7 (−10.7) | 19.5 (+1.2) | 19.1 (801) | −7.4 [−10.3, −4.6] | −2.8 [−4.8, −0.7] | −6.6 [−10.6, −3.1] |
| GPT-6 astra | 27.6 (+16.4) | 22.4 | 22.5 (−7.7) | 19.0 (+5.3) | 19.0 (802) | −8.6 [−11.3, −6.1] | −3.4 [−5.3, −1.5] | −8.8 [−12.7, −5.1] |
| Gemini 3.8 Flash | 21.9 (+7.9) | 20.4 | 18.5 (−8.1) | 16.7 (−2.2) | 16.7 (802) | −5.2 [−7.5, −3.1] | −3.7 [−5.2, −2.3] | −5.4 [−8.4, −2.8] |
| Gemini 4 Argon | 27.9 (+17.4) | 22.6 | 21.2 (+2.7) | 18.2 (+3.0) | 18.2 (802) | −9.6 [−12.3, −7.2] | −4.4 [−6.2, −2.6] | −7.7 [−11.2, −4.4] |

<<TABLE3>>
| Model | (1) Before, simple prompt | (3b) Before, structured prompt | (3a) Both photos, simple prompt | (3) Both photos, structured prompt | Photo effect, structured prompt (3) − (3b) | Photo effect, simple prompt (3a) − (1) | Prompt effect, before only (3b) − (1) | Prompt effect, both photos (3) − (3a) |
|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | 24.7 (−6.7) | 26.2 (−17.8) | 25.0 (−14.3) | 24.9 (−14.0) | −1.3 [−2.8, +0.4] | +0.2 [−1.9, +2.2] | +1.5 [−0.3, +3.2] | −0.1 [−1.6, +1.4] |
| Sonnet 5.5 | 24.2 (+0.9) | 26.9 (−1.3) | 18.9 (−8.0) | 21.8 (−2.9) | −5.1 [−9.3, −1.3] | −5.3 [−8.1, −3.0] | +2.7 [−1.3, +6.9] | +2.9 [+1.2, +4.6] |
| Opus 5.5 | 30.1 (+21.7) | 22.9 (+9.2) | 20.3 (+6.3) | 20.5 (+9.0) | −2.5 [−4.4, −0.6] | −9.7 [−13.4, −6.5] | −7.1 [−9.8, −4.9] | +0.1 [−0.7, +1.1] |
| GPT-6 luna | 23.9 (+4.3) | 23.5 (+3.7) | 20.7 (−7.1) | 21.0 (−6.1) | −2.5 [−4.1, −1.0] | −3.1 [−5.1, −1.4] | −0.4 [−1.5, +0.7] | +0.3 [−0.7, +1.3] |
| GPT-6.1 sol | 26.9 (+14.8) | 26.2 (+17.0) | 18.7 (−2.2) | 19.5 (+1.2) | −6.7 [−9.6, −3.8] | −8.2 [−11.1, −5.6] | −0.7 [−1.5, +0.2] | +0.8 [−0.2, +2.1] |
| GPT-6 astra | 27.6 (+16.4) | 27.2 (+19.1) | 18.4 (+1.6) | 19.0 (+5.3) | −8.1 [−10.9, −5.6] | −9.2 [−12.1, −6.6] | −0.5 [−1.4, +0.4] | +0.6 [+0.0, +1.2] |
| Gemini 3.8 Flash | 21.9 (+7.9) | 21.9 (+9.6) | 16.8 (−4.3) | 16.7 (−2.2) | −5.3 [−7.8, −3.2] | −5.1 [−7.4, −2.9] | +0.1 [−0.7, +0.9] | −0.2 [−0.9, +0.6] |
| Gemini 4 Argon | 27.9 (+17.4) | 23.5 (−5.4) | 19.0 (−1.7) | 18.2 (+3.0) | −5.3 [−7.2, −3.3] | −8.8 [−11.7, −6.0] | −4.4 [−7.3, −1.4] | −0.8 [−1.9, +0.2] |

<<ABL_DAY_TEXT>>
**Day level for the ablation conditions** (mean e_day %; 95% LoA; days within 800 kJ %). (1) / (3b) / (3a) / (3): Haiku 5.5 −4.2, −48..+39, 34 / −15.5, −49..+18, 28 / −12.5, −54..+29, 32 / −12.0, −53..+29, 29. Sonnet 5.5 +5.5, −62..+73, 37 / −0.4, −63..+62, 40 / −5.7, −36..+24, 41 / −0.6, −41..+40, 41. Opus 5.5 +25.4, −32..+83, 25 / +12.5, −33..+58, 33 / +8.0, −25..+41, 50 / +12.0, −25..+49, 43. GPT-6 luna +6.7, −41..+54, 39 / +6.0, −40..+52, 32 / −5.7, −39..+27, 39 / −4.3, −38..+30, 43. GPT-6.1 sol +17.7, −33..+69, 29 / +20.0, −31..+71, 28 / −0.5, −31..+30, 48 / +3.4, −31..+38, 51. GPT-6 astra +20.2, −31..+71, 24 / +22.5, −27..+72, 25 / +3.7, −29..+36, 47 / +7.6, −27..+42, 45. Gemini 3.8 Flash +10.6, −36..+57, 39 / +12.5, −34..+59, 37 / −2.1, −28..+24, 53 / −0.5, −28..+27, 57. Gemini 4 Argon +20.4, −32..+72, 28 / −3.5, −42..+35, 36 / −0.5, −31..+30, 47 / +4.5, −25..+34, 55.

<<TABLE4>>
| Model | Estimate − served | Energy left | Estimate − eaten | Meals with ≥10% left where the two parts offset* | Median offset, kcal |
|---|---|---|---|---|---|
| Haiku 5.5 | −156 | +103 | −53 | 178 / 292 | 153 |
| Sonnet 5.5 | −104 | +103 | −1 | 146 / 292 | 147 |
| Opus 5.5 | +38 | +103 | +141 | 61 / 292 | 126 |
| GPT-6 luna | −80 | +103 | +23 | 141 / 292 | 153 |
| GPT-6.1 sol | −8 | +103 | +95 | 84 / 292 | 141 |
| GPT-6 astra | +4 | +103 | +107 | 88 / 292 | 126 |
| Gemini 3.8 Flash | −55 | +103 | +48 | 111 / 292 | 140 |
| Gemini 4 Argon | +12 | +103 | +115 | 71 / 292 | 133 |

<<TABLE5>>
| Model, input | Mean day error % | 90% CI | Equivalence | 95% LoA % | Days within 800 kJ % |
|---|---|---|---|---|---|
| Haiku 5.5, before only | −4.2 [−8.9, +0.7] | −8.1, −0.3 | yes | −48 to +39 | 34 |
| Haiku 5.5, both photos | −12.0 [−16.2, −7.2] | −15.7, −8.2 | no | −53 to +29 | 29 |
| Sonnet 5.5, before only | +5.5 [−0.7, +12.3] | +0.1, +11.0 | no | −62 to +73 | 37 |
| Sonnet 5.5, both photos | −0.6 [−4.2, +3.2] | −3.7, +2.5 | yes | −41 to +40 | 41 |
| Opus 5.5, before only | +25.4 [+19.4, +32.3] | +20.3, +31.0 | no | −32 to +83 | 25 |
| Opus 5.5, both photos | +12.0 [+8.7, +15.5] | +9.2, +14.8 | no | −25 to +49 | 43 |
| GPT-6 luna, before only | +6.7 [+1.9, +11.8] | +2.6, +10.9 | no | −41 to +54 | 39 |
| GPT-6 luna, both photos | −4.3 [−7.4, −1.0] | −6.9, −1.5 | yes | −38 to +30 | 43 |
| GPT-6.1 sol, before only | +17.7 [+12.6, +23.4] | +13.1, +22.5 | no | −33 to +69 | 29 |
| GPT-6.1 sol, both photos | +3.4 [+0.3, +6.5] | +0.8, +6.0 | yes | −31 to +38 | 51 |
| GPT-6 astra, before only | +20.2 [+15.0, +25.9] | +15.6, +25.0 | no | −31 to +71 | 24 |
| GPT-6 astra, both photos | +7.6 [+4.4, +10.8] | +5.0, +10.3 | no | −27 to +42 | 45 |
| Gemini 3.8 Flash, before only | +10.6 [+5.8, +16.0] | +6.4, +15.0 | no | −36 to +57 | 39 |
| Gemini 3.8 Flash, both photos | −0.5 [−2.9, +2.0] | −2.5, +1.6 | yes | −28 to +27 | 57 |
| Gemini 4 Argon, before only | +20.4 [+14.9, +26.4] | +15.8, +25.4 | no | −32 to +72 | 28 |
| Gemini 4 Argon, both photos | +4.5 [+1.9, +7.1] | +2.3, +6.7 | yes | −25 to +34 | 55 |

<<APPC>>
| Model | Before only | Subtraction | Both photos |
|---|---|---|---|
| Haiku 5.5 | −4.2 [−8.9, +0.7]; −48 to +39; 34 | −32.9 [−35.7, −30.3]; −62 to −4; 8 | −12.0 [−16.2, −7.2]; −53 to +29; 29 |
| Sonnet 5.5 | +5.5 [−0.7, +12.3]; −62 to +73; 37 | −16.1 [−18.8, −13.4]; −48 to +15; 28 | −0.6 [−4.2, +3.2]; −41 to +40; 41 |
| Opus 5.5 | +25.4 [+19.4, +32.3]; −32 to +83; 25 | +3.7 [+0.9, +6.5]; −29 to +37; 49 | +12.0 [+8.7, +15.5]; −25 to +49; 43 |
| GPT-6 luna | +6.7 [+1.9, +11.8]; −41 to +54; 39 | −16.5 [−19.4, −13.5]; −49 to +16; 22 | −4.3 [−7.4, −1.0]; −38 to +30; 43 |
| GPT-6.1 sol | +17.7 [+12.6, +23.4]; −33 to +69; 29 | −9.4 [−12.5, −6.3]; −43 to +24; 30 | +3.4 [+0.3, +6.5]; −31 to +38; 51 |
| GPT-6 astra | +20.2 [+15.0, +25.9]; −31 to +71; 24 | −5.5 [−8.5, −2.6]; −38 to +27; 42 | +7.6 [+4.4, +10.8]; −27 to +42; 45 |
| Gemini 3.8 Flash | +10.6 [+5.8, +16.0]; −36 to +57; 39 | −6.5 [−8.8, −4.2]; −33 to +20; 49 | −0.5 [−2.9, +2.0]; −28 to +27; 57 |
| Gemini 4 Argon | +20.4 [+14.9, +26.4]; −32 to +72; 28 | +3.9 [+1.4, +6.5]; −25 to +33; 45 | +4.5 [+1.9, +7.1]; −25 to +34; 55 |

<<LOA_CI_TEXT>>
Bootstrap 95% CIs of the day-level limits of agreement, both photos: Haiku 5.5 lower [−66, −42], upper [+13, +48]; Sonnet 5.5 lower [−47, −35], upper [+30, +49]; Opus 5.5 lower [−30, −19], upper [+39, +57]; GPT-6 luna lower [−43, −33], upper [+22, +36]; GPT-6.1 sol lower [−35, −26], upper [+30, +45]; GPT-6 astra lower [−31, −22], upper [+35, +49]; Gemini 3.8 Flash lower [−32, −23], upper [+20, +32]; Gemini 4 Argon lower [−28, −21], upper [+28, +39].

<<TABLE7>>
| Model | Protein | Carbohydrate | Fat |
|---|---|---|---|
| Haiku 5.5 | −29 (−70 to +12) | +1 (−40 to +43) | −12 (−52 to +29) |
| Sonnet 5.5 | −24 (−62 to +14) | +14 (−33 to +62) | +3 (−39 to +45) |
| Opus 5.5 | −8 (−52 to +37) | +25 (−24 to +75) | +18 (−33 to +70) |
| GPT-6 luna | −16 (−63 to +30) | +12 (−31 to +55) | +0 (−45 to +46) |
| GPT-6.1 sol | −13 (−57 to +30) | +16 (−26 to +58) | +7 (−36 to +51) |
| GPT-6 astra | −10 (−54 to +35) | +21 (−23 to +64) | +12 (−31 to +56) |
| Gemini 3.8 Flash | −20 (−53 to +13) | +11 (−25 to +47) | +5 (−35 to +45) |
| Gemini 4 Argon | −3 (−46 to +40) | +11 (−29 to +51) | +10 (−34 to +54) |

<<APPD_RECAL>>
| Model | Meal MAE%: none → cal | Day mean %: none → cal | Day 95% LoA: none → cal | Days within 800 kJ %: none → cal |
|---|---|---|---|---|
| Haiku 5.5 | 24.9 → 25.0 | −12.0 → −4.5 | −53..+29 → −50..+41 | 29 → 32 |
| Sonnet 5.5 | 21.8 → 23.2 | −0.7 → −0.9 | −41..+40 → −42..+41 | 41 → 39 |
| Opus 5.5 | 20.5 → 19.1 | +12.1 → +0.5 | −25..+49 → −33..+34 | 43 → 43 |
| GPT-6 luna | 21.0 → 22.3 | −4.2 → −1.9 | −38..+29 → −37..+34 | 43 → 40 |
| GPT-6.1 sol | 19.5 → 20.8 | +3.4 → −1.1 | −31..+38 → −36..+33 | 51 → 41 |
| GPT-6 astra | 19.1 → 19.3 | +7.7 → −1.1 | −27..+43 → −34..+32 | 45 → 42 |
| Gemini 3.8 Flash | 16.6 → 17.8 | −0.5 → −1.0 | −27..+26 → −29..+27 | 57 → 52 |
| Gemini 4 Argon | 18.2 → 18.9 | +4.5 → +0.1 | −25..+34 → −29..+29 | 56 → 47 |

<<APPD_MEAL>>
| Model | Breakfast (n = 286) | Lunch (n = 257) | Dinner (n = 259) |
|---|---|---|---|
| Haiku 5.5 | 19.0 / −6.7 | 22.4 / −6.2 | 31.4 / −25.8 |
| Sonnet 5.5 | 18.3 / +3.1 | 18.8 / −1.6 | 26.9 / −8.6 |
| Opus 5.5 | 20.6 / +12.1 | 20.0 / +12.3 | 20.8 / +4.1 |
| GPT-6 luna | 19.1 / −3.5 | 19.5 / +1.8 | 23.8 / −14.3 |
| GPT-6.1 sol | 19.8 / +5.0 | 18.2 / +10.0 | 20.4 / −8.7 |
| GPT-6 astra | 20.3 / +8.8 | 17.9 / +11.7 | 19.0 / −2.4 |
| Gemini 3.8 Flash | 15.9 / +1.6 | 15.2 / +5.3 | 18.4 / −11.2 |
| Gemini 4 Argon | 19.9 / +8.7 | 17.8 / +4.0 | 17.3 / −2.2 |

<<APPF_FIXED>>
| Model | MAE% before×c / both | Δ both − before×c, all [95% CI] | Δ, ≥10% left [95% CI] | Day mean %: before×c / both | Day LoA %: before×c / both | Days within 800 kJ %: before×c / both |
|---|---|---|---|---|---|---|
| Haiku 5.5 | 27.3 / 24.9 | −2.5 [−4.2, −0.6] | −1.8 [−4.4, +0.6] | −16.6 / −12.0 | −55..+22 / −53..+29 | 28 / 29 |
| Sonnet 5.5 | 24.9 / 21.8 | −3.0 [−5.5, −0.8] | −1.3 [−5.9, +2.7] | −8.2 / −0.6 | −67..+51 / −41..+40 | 32 / 41 |
| Opus 5.5 | 22.7 / 20.5 | −2.2 [−4.8, +0.3] | −7.5 [−12.3, −3.3] | +9.2 / +12.0 | −41..+60 / −25..+49 | 35 / 43 |
| GPT-6 luna | 23.7 / 21.0 | −2.6 [−4.2, −1.1] | −1.3 [−5.1, +1.9] | −7.1 / −4.3 | −48..+34 / −38..+30 | 27 / 43 |
| GPT-6.1 sol | 22.3 / 19.5 | −2.8 [−4.8, −0.7] | −6.6 [−10.6, −3.1] | +2.5 / +3.4 | −42..+47 / −31..+38 | 41 / 51 |
| GPT-6 astra | 22.4 / 19.0 | −3.4 [−5.3, −1.5] | −8.8 [−12.7, −5.1] | +4.7 / +7.6 | −40..+49 / −27..+42 | 40 / 45 |
| Gemini 3.8 Flash | 20.4 / 16.7 | −3.7 [−5.2, −2.3] | −5.4 [−8.4, −2.8] | −3.7 / −0.5 | −45..+37 / −28..+27 | 41 / 57 |
| Gemini 4 Argon | 22.6 / 18.2 | −4.4 [−6.2, −2.6] | −7.7 [−11.2, −4.4] | +4.8 / +4.5 | −41..+50 / −25..+34 | 39 / 55 |

<<APPF_KCAL>>
| Model | ≥10% left | <10% left | Difference |
|---|---|---|---|
| Haiku 5.5 | −28 [−47, −8] | +20 [+4, +40] | −48 [−75, −22] |
| Sonnet 5.5 | −43 [−78, −9] | +2 [−21, +21] | −45 [−87, −3] |
| Opus 5.5 | −145 [−181, −110] | −8 [−29, +8] | −138 [−178, −97] |
| GPT-6 luna | −45 [−76, −14] | −1 [−10, +7] | −43 [−74, −12] |
| GPT-6.1 sol | −116 [−147, −84] | −3 [−16, +13] | −113 [−146, −79] |
| GPT-6 astra | −135 [−166, −102] | −8 [−16, −0] | −127 [−157, −93] |
| Gemini 3.8 Flash | −90 [−116, −63] | +2 [−5, +9] | −92 [−119, −64] |
| Gemini 4 Argon | −134 [−163, −102] | −20 [−31, −9] | −114 [−146, −82] |

<<APPF_PILOT_TEXT>>
**Without the pilot.** Excluding the 100 pilot meals leaves 702 meals and 100 complete days; excluding all pilot participants leaves 371 meals and 64 complete days. MAE% change (both − before), all meals: Haiku 5.5 +0.3 / −0.8, Sonnet 5.5 −3.1 / −2.7, Opus 5.5 −10.0 / −10.4, GPT-6 luna −2.3 / −3.3, GPT-6.1 sol −7.3 / −7.9, GPT-6 astra −8.7 / −9.3, Gemini 3.8 Flash −5.0 / −4.7, Gemini 4 Argon −9.6 / −10.5.

<<APPF_PAIRS_TEXT>>
**Between-model differences in Δ MAE% (both − before), all 28 pairs, unadjusted [95% CI].** Haiku−Sonnet +2.5 [−0.1, +5.2]; Haiku−Opus +9.7 [+6.7, +12.9]; Haiku−luna +3.0 [+1.0, +5.1]; Haiku−sol +7.5 [+4.9, +10.3]; Haiku−astra +8.7 [+6.5, +11.2]; Haiku−Flash +5.4 [+3.2, +7.7]; Haiku−Argon +9.8 [+7.4, +12.5]; Sonnet−Opus +7.2 [+3.7, +10.7]; Sonnet−luna +0.4 [−2.3, +2.9]; Sonnet−sol +5.0 [+2.3, +7.5]; Sonnet−astra +6.2 [+3.5, +8.6]; Sonnet−Flash +2.8 [+0.2, +5.3]; Sonnet−Argon +7.2 [+4.5, +9.9]; Opus−luna −6.8 [−9.5, −4.2]; Opus−sol −2.2 [−4.8, −0.0]; Opus−astra −1.0 [−3.3, +1.0]; Opus−Flash −4.4 [−6.7, −2.4]; Opus−Argon +0.1 [−2.4, +2.3]; luna−sol +4.5 [+2.1, +6.9]; luna−astra +5.8 [+3.9, +7.8]; luna−Flash +2.4 [+0.7, +4.2]; luna−Argon +6.8 [+5.0, +8.8]; sol−astra +1.2 [−0.0, +2.7]; sol−Flash −2.1 [−3.7, −0.4]; sol−Argon +2.3 [+0.2, +4.7]; astra−Flash −3.4 [−4.7, −2.2]; astra−Argon +1.1 [−0.6, +2.7]; Flash−Argon +4.4 [+2.9, +6.0].

<<HETERO_TEXT>>
range of Δ across models 9.8 points [+7.9, +13.0]; SD 3.5 [+2.7, +4.4]; 7 of 8 negative

<<APPF_RM_TEXT>>
**Day-level agreement, repeated-measures and log-scale** (both photos). Within-participant SD of e_day / ICC / ratio LoA (estimate ÷ truth): Haiku 5.5 16.3 / 0.41 / ×0.57–×1.30; Sonnet 5.5 18.3 / 0.22 / ×0.67–×1.42; Opus 5.5 12.9 / 0.53 / ×0.81–×1.51; GPT-6 luna 13.3 / 0.40 / ×0.67–×1.33; GPT-6.1 sol 13.4 / 0.43 / ×0.74–×1.41; GPT-6 astra 12.7 / 0.49 / ×0.78–×1.46; Gemini 3.8 Flash 11.0 / 0.37 / ×0.76–×1.29; Gemini 4 Argon 13.8 / 0.15 / ×0.78–×1.37. ICC range 0.15 to 0.53.

<<SHRINK_TEXT>>
Haiku 5.5 meal 0.68, day 0.76, −14.7 pts per doubling; Sonnet 5.5 meal 0.75, day 0.78, −14.6 pts per doubling; Opus 5.5 meal 0.76, day 0.74, −21.5 pts per doubling; GPT-6 luna meal 0.72, day 0.78, −15.0 pts per doubling; GPT-6.1 sol meal 0.69, day 0.77, −17.5 pts per doubling; GPT-6 astra meal 0.71, day 0.75, −20.0 pts per doubling; Gemini 3.8 Flash meal 0.78, day 0.83, −12.3 pts per doubling; Gemini 4 Argon meal 0.84, day 0.86, −10.8 pts per doubling

<<APPF_PROTEIN_TEXT>>
**Protein error and meal composition** (both photos; Spearman with protein density g/100 kcal, Spearman with animal-source energy share; bias in meals with animal share <1/3 vs ≥1/3): Haiku 5.5 −0.50, −0.35; −20% vs −37%. Sonnet 5.5 −0.50, −0.31; −16% vs −31%. Opus 5.5 −0.46, −0.27; −2% vs −15%. GPT-6 luna −0.47, −0.24; −13% vs −24%. GPT-6.1 sol −0.41, −0.11; −12% vs −20%. GPT-6 astra −0.38, −0.10; −9% vs −15%. Gemini 3.8 Flash −0.42, −0.20; −15% vs −26%. Gemini 4 Argon −0.38, −0.09; −2% vs −8%.

<<PROTEIN_RANGES>>
protein bias −34% to −7%; Spearman density −0.38 to −0.50; animal share −0.09 to −0.35

<<APPF_GRAMS_TEXT>>
**Grams eaten from (3a)** (MAE g; error relative to mean true grams; bias): Haiku 5.5 274 g, 37.9%, −36.7%; Sonnet 5.5 185 g, 25.6%, −21.9%; Opus 5.5 149 g, 20.6%, −11.9%; GPT-6 luna 268 g, 37.1%, −36.0%; GPT-6.1 sol 183 g, 25.2%, −21.9%; GPT-6 astra 171 g, 23.6%, −19.5%; Gemini 3.8 Flash 166 g, 23.0%, −20.4%; Gemini 4 Argon 135 g, 18.6%, −12.5%.

<<APPF_RETEST_TEXT>>
**Test–retest, condition (3), 100 pilot meals, three calls** (MAE% per call; median per-meal CV; mean absolute difference between two calls as % of truth): Haiku 5.5 29.3 / 28.8 / 28.2; 8.2%; 11.4%. Sonnet 5.5 21.4 / 21.4 / 20.1; 4.6%; 8.2% (96 meals parsed in all three). Opus 5.5 23.3 / 21.9 / 23.1; 5.9%; 8.7%. GPT-6 luna 23.7 / 22.4 / 23.5; 7.6%; 11.9% (99 meals parsed in all three). GPT-6.1 sol 20.5 / 20.7 / 21.2; 3.5%; 6.6%. GPT-6 astra 20.5 / 21.0 / 21.1; 3.8%; 6.1%. Gemini 3.8 Flash 18.9 / 19.8 / 19.4; 4.7%; 7.5%. Gemini 4 Argon 18.8 / 20.2 / 19.4; 4.2%; 8.5%.

<<RETEST_RANGES>>
max within-model MAE% range 1.4; median CV 3.5–8.2%; pairwise difference 6.1–11.9%

<<APPF_EFFORT_TEXT>>
**Reasoning effort, condition (3), same 100 meals** (MAE% low, mean of three calls → high; bias low → high; cost per meal, high relative to low): Haiku 5.5 28.8 → 24.6; −15.7 → −12.6; ×1.7. Sonnet 5.5 21.0 → 20.7; −7.3 → −9.3; ×1.1. Opus 5.5 22.7 → 22.3; +7.5 → +4.7; ×1.2. GPT-6 luna 23.2 → 24.1; −7.6 → −8.4; ×2.2. GPT-6.1 sol 20.8 → 21.1; −1.9 → −0.3; ×2.5. GPT-6 astra 20.9 → 21.4; +3.1 → +3.1; ×2.6. Gemini 3.8 Flash 19.4 → 19.2; −6.3 → −6.7; ×3.4. Gemini 4 Argon 19.5 → 19.4; −0.7 → +0.7; ×4.3.

<<EFFORT_DELTAS>>
Haiku 5.5 −4.2 (×1.7); Sonnet 5.5 −0.3 (×1.1); Opus 5.5 −0.4 (×1.2); GPT-6 luna +0.9 (×2.2); GPT-6.1 sol +0.3 (×2.5); GPT-6 astra +0.6 (×2.6); Gemini 3.8 Flash −0.1 (×3.4); Gemini 4 Argon −0.0 (×4.3)

<<APPF_VALID_TEXT>>
**Valid-output subset** (meals parsed in all three conditions for that model): MAE% before / subtraction / both — Haiku 5.5 (n = 800) 24.7 / 36.5 / 24.1; Sonnet 5.5 (n = 789) 23.1 / 24.9 / 19.3; Opus 5.5 (n = 801) 29.4 / 21.0 / 20.5; GPT-6 luna (n = 802) 23.9 / 26.2 / 21.0; GPT-6.1 sol (n = 801) 26.9 / 23.8 / 19.1; GPT-6 astra (n = 802) 27.6 / 22.5 / 19.0; Gemini 3.8 Flash (n = 802) 21.9 / 18.5 / 16.7; Gemini 4 Argon (n = 802) 27.9 / 21.2 / 18.2.

<<FAILS>>
Haiku 5.5 0/0/2 (before/subtraction/both); Sonnet 5.5 2/2/11 (before/subtraction/both); Opus 5.5 1/1/0 (before/subtraction/both); GPT-6 luna 0/0/0 (before/subtraction/both); GPT-6.1 sol 0/0/1 (before/subtraction/both); GPT-6 astra 0/0/0 (before/subtraction/both); Gemini 3.8 Flash 0/0/0 (before/subtraction/both); Gemini 4 Argon 0/0/0 (before/subtraction/both)

<<SERVED_LEFTOVER_TEXT>>
Both-photos reading of served energy and of energy left (total estimate vs total truth, meals with served defined): Haiku 5.5 served −17.0%, leftover −28%; Sonnet 5.5 served −8.6%, leftover −25%; Opus 5.5 served +8.3%, leftover +5%; GPT-6 luna served −5.4%, leftover −1%; GPT-6.1 sol served +2.0%, leftover +11%; GPT-6 astra served +6.0%, leftover +11%; Gemini 3.8 Flash served −3.8%, leftover −14%; Gemini 4 Argon served +1.2%, leftover −10%.

