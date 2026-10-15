"""compA_v2: compA_v1 + disagreement-dependent shrinkage term in the calibration.

Components (tag):
  view R  [invariant] rsn_v6 structured written reasoning (vessel -> per-item area % -> volume -> ONE bulk density
          -> kcal), 2 chains (medium s0, low s0), geometric mean. Prompt byte-identical to gen1 rsn_v11.
  view DN [domain]+[dataset] den_v4 density/identification rules (egg whites vs feta, olives, sweet potato;
          as-served kcal/100 g references) with greens flag; OIL_FRAC=0.09 dressing oil per g raw greens is
          [dataset] (fitted by gen1 on search labels). medium s0 (retry s10/s20). Byte-identical to den_v7 PROMPT_B.
  view P  [dataset] ens_v5 direct-total prompt with plate ruler + cafeteria small-serving prior text,
          3 samples (low s0..s2), geometric mean. Byte-identical to ens_v11 PRIOR.
  Why these three: lowest pairwise log-error correlations among the cheap gen1 views on search-300
  (R-DN 0.50, R-P 0.65, DN-P 0.66; vs R-G 0.87, G-D 0.83); geometry views (geo_v5 trio, cal_v3) and the
  plain direct view got ~0 stacked weight once R+DN+P were present (g2 cv: +Gp 30.71 vs 30.66, +D0 30.66).
  calibration [dataset] ONE post-hoc map on the three view logs:
     kcal = REF*exp(C + sum W_i*ln(v_i/REF) + A*m*sd + B*sd, m/sd = mean/pop-sd of the three logs (views disagree -> pull toward the centre))
  fitted by Nelder-Mead minimising sum|est-true| (= mae_pct_of_mean) on the 600 rows of
  search --n 600 --seed g2 ONLY (5-fold x4 cv on the same rows given below). sum W < 1 = shrinkage
  (estimates are over-dispersed, slope ~0.75 per gen1). A failed view is imputed by the mean of the others.
  DIS=(A,B) fitted jointly with C,W. g2 in-sample 29.90, cv 30.42. Cost ~3.0 m$/dish (measured on g2b).
"""
import json, re, math

MODEL = "claude-haiku-5-5"
REF = 300.0
OIL_FRAC = 0.09
C = 0.0313
W = [0.6095, 0.2967, 0.1497]          # weights for (R, DN, P)
DIS = [-0.6419, -0.3426]

P_RSN = """This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.
Work through these steps in writing, briefly, before giving the answer.

STEP 1 - Scene: what kind of meal is this? (Do not guess a total weight yet.)
STEP 2 - Vessel: identify the plate/bowl and its likely diameter in cm (dinner plate ~26 cm, side plate
~20 cm, cereal bowl ~15 cm, small dish ~8 cm). Vessel area = 3.14 x (diameter/2)^2. Food on other
plates at the edge of the photo is not part of this meal.
STEP 3 - Items: list every distinct visible food, including oil, dressing or sauce when you can see them.
STEP 4 - Area: for each item, the percent of the vessel area it covers. These percents must add up to the
share of the vessel actually covered by food (check this; if food covers most of the plate they should
add up to most of 100%).
STEP 5 - Volume: area (cm^2) x typical height (cm) = gross volume in ml, measured as the outer envelope
of the pile. Do not reduce it here.
STEP 6 - Grams: gross volume x bulk density. The bulk density already accounts for air and gaps, so this
is the ONLY reduction factor - do not apply any other gap or airy factor. Typical bulk densities (g/ml):
loose leafy greens 0.1-0.2, cut vegetables / fruit pieces 0.5-0.7, rice / pasta / grains 0.8,
mashed or dense items, meat, fish, egg, cheese, bread-like slices 0.9-1.0 (bread loaf ~0.3), sauces 1.0.
STEP 7 - Energy: kcal per 100 g for each item as plated (cooked weight); multiply.
STEP 8 - Sanity check: is the total plausible for what is visible? Small amounts (a few leaves, a spoon of
rice) must get small weights; a fully covered dinner plate usually holds several hundred grams.
Estimate only what is visible; do not assume a typical serving.

Two worked examples (generic, only to show the arithmetic and the range of scales):

Example A (small): side plate 20 cm, area 314 cm^2, food covers ~15%. Cherry tomatoes 6% = 19 cm^2 x 2.5 cm
= 47 ml x 0.6 = 28 g x 18 kcal/100g = 5 kcal. Cheese slice 9% = 28 cm^2 x 0.3 cm = 8 ml x 1.0 = 8 g
x 400 kcal/100g = 32 kcal. Total 36 g, 37 kcal.

Example B (large): dinner plate 26 cm, area 530 cm^2, food covers ~85%. Cooked rice 30% = 159 cm^2 x 2 cm
= 318 ml x 0.8 = 254 g x 130 = 330 kcal. Grilled chicken pieces 20% = 106 cm^2 x 1.5 cm = 159 ml x 1.0
= 159 g x 165 = 262 kcal. Mixed leaves 30% = 159 cm^2 x 3 cm = 477 ml x 0.15 = 72 g x 20 = 14 kcal.
Roasted vegetables 5% = 27 cm^2 x 2 cm = 53 ml x 0.6 = 32 g x 60 = 19 kcal. Oil sheen ~5 g x 880 = 44 kcal.
Total 522 g, 669 kcal.

Then, on the last line, write ANSWER: followed by JSON only:
{"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

P_DEN = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.

Then give kcal per 100 g for each item as served:
- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);
  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are
  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.
- Fat: raw leafy greens (lettuce, mixed greens, arugula, spinach, kale, chard) get "greens": true; their
  dressing is added automatically, so do not list a dressing for them. Cooked vegetables are 25-50 and get no
  oil item unless oil is visibly pooled. Other visible sauce, butter, cheese or oil: add as its own item.
- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,
  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,
  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>, "greens": <true|false>}]}"""

P_PRIOR = """This is an overhead photo of a single cafeteria serving on a plate or in a bowl.
Use the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).
Think about how much food is really there: many of these servings are small (a few pieces, a thin layer),
and the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.
Estimate the total weight of food you can see and its total food energy, including visible oil or sauce.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


RSN_CALLS = [(P_RSN, "medium", [0]), (P_RSN, "low", [0])]
DEN_CALLS = [(P_DEN, "medium", [0, 10, 20])]
PRIOR_CALLS = [(P_PRIOR, "low", [0]), (P_PRIOR, "low", [1]), (P_PRIOR, "low", [2])]


def _json(text, anchor=None):
    if anchor:
        i = text.rfind("ANSWER:")
        tail = text[i:] if i >= 0 else text
        j = tail.find(anchor)
        if j < 0:
            tail, j = text, text.rfind(anchor)
        text = tail[j:]
    return json.loads(re.search(r"\{.*\}", text, re.S).group(0))


def _items(d, oil_frac=0.0):
    items = d["items"]
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    oil = oil_frac * sum(float(i["grams"]) for i in items if i.get("greens") is True)
    return k + oil * 8.84, g + oil


def _rsn(t):
    return _items(_json(t, '{"items"'))


def _den(t):
    return _items(_json(t), OIL_FRAC)


def _prior(t):
    d = _json(t)
    return float(d["kcal"]), float(d.get("mass_g") or 0)


def _gm(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def _view(llm, image, calls, fn):
    ks, ms = [], []
    for prompt, effort, samples in calls:
        for s in samples:
            try:
                k, m = fn(llm.ask(prompt, image, model=MODEL, effort=effort, sample=s, max_tokens=8000))
            except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                continue
            if k > 0:
                ks.append(k)
                ms.append(m)
                break
    return _gm(ks), _gm(ms)


def estimate(image, llm):
    views = [_view(llm, image, c, fn) for c, fn in
             ((RSN_CALLS, _rsn), (DEN_CALLS, _den), (PRIOR_CALLS, _prior))]
    ok = [math.log(k / REF) for k, _ in views if k]
    if not ok:
        raise ValueError("no view parsed")
    mean = sum(ok) / len(ok)
    x = [math.log(k / REF) if k else mean for k, _ in views]  # a failed view is imputed by the others' mean
    z = C + sum(w * xi for w, xi in zip(W, x))
    if DIS:
        sd = math.sqrt(sum((xi - mean) ** 2 for xi in x) / len(x))
        z += DIS[0] * mean * sd + DIS[1] * sd
    return {"kcal": REF * math.exp(z), "mass_g": _gm([m for _, m in views])}
