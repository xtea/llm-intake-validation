"""E_v3 (gen3 mutator E): compA_v4 minus its redundant 2nd reasoning chain, plus compC's geometry-observation
view. 6 Haiku calls, ~2.1 m$/dish (compA_v4: 6 calls, ~2.8 m$). Prompts byte-identical to gen2 (cache reuse).
kcal = REF*exp(C + WM*mean ln(v/REF)) over the 4 views: equal weights, 2 fitted constants.
 R0 [invariant] rsn_v6 written procedure (vessel, item area %, volume, ONE bulk density); ONE chain, low.
    The dropped medium chain has r .96 with this one (log error); dropping it costs ~+0.1, saves 0.9 m$.
 DN [domain] den_v4 look-alike/density rules + greens flag; OIL_FRAC .09 dressing on greens [dataset]; medium
 P  [dataset] ens_v5 direct total with cafeteria small-serving prior; 3 samples (low s0..s2), geo mean
    (resampling P matters here: 1 sample is +0.45 worse on never-seen dishes)
 G  [invariant] compC geo_v1 observation-only geometry, grams in code; FRAME_CM=45 fixed rig [dataset]; medium.
    2nd-least correlated view with the compA composite (r .71; household-unit counting U .67, but U's MAE gain
    did not hold on dishes outside earlier samples, see E_v1/E_v2).
Fit [dataset]: C, WM by coordinate search min sum|est-true| on the 597 g3 rows (search --n 600 --seed g3)
with all views parsed: C=-0.0791 WM=0.9422; in-sample 30.62, 5-fold cv 30.77 (R+DN+P refit: 31.29).
Failed view = mean of the others.g3b-unseen (380): 31.62 vs compA views refit on g3 31.54 (tie at ~75% of the cost); composition chosen after
looking at g3b rows, so this is not a clean confirmation.
"""
import json, re, math

MODEL = "claude-haiku-5-5"
REF = 300.0
C = -0.0791
WM = 0.9422
FRAME_CM = 45.0
SHRINK = 0.85
OIL_FRAC = 0.09

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

_H = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.

Then give kcal per 100 g for each item as served:
- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);
  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are
  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.
- Fat: """
_REF = """- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,
  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,
  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600."""
_RJ = "\nReply with JSON only: {\"items\": [{\"name\": \"...\", \"grams\": <number>, \"kcal_per_100g\": <number"
P_DN = _H + "raw leafy greens (lettuce, mixed greens, arugula, spinach, kale, chard) get \"greens\": true; their\n  dressing is added automatically, so do not list a dressing for them. Cooked vegetables are 25-50 and get no\n  oil item unless oil is visibly pooled. Other visible sauce, butter, cheese or oil: add as its own item.\n" + _REF + _RJ + ">, \"greens\": <true|false>}]}"

P_GEO = """This is an overhead photo (camera pointing straight down) of a cafeteria meal.
Do NOT estimate grams directly. Report geometric observations only; the weight is computed from them.

1. The vessel: is the food on a plate, in a bowl, or on a tray/none? Estimate the vessel's rim diameter as a
   fraction of the image WIDTH (0-1), and its real diameter in cm (dinner plate ~26, side plate ~20, bowl ~15).
2. For each distinct food item (include visible oil, butter, dressing or sauce as their own items):
   - "kind": "pieces" if it is discrete countable units (eggs, slices, nuggets, cookies, fruit pieces, sushi),
     otherwise "pile" (rice, salad, stew, mash, spread-out food).
   - "count" and "piece_g" (typical weight of ONE such piece of the size you see) for pieces.
   - "footprint": fraction of the vessel's area the item covers when viewed from above (0-1).
     Be literal: a few leaves may be 0.02, a spoon of sauce 0.01, half the plate 0.5.
   - "height_cm": average thickness/height of the item layer (a sauce smear 0.2, a slice of meat 1, a rice mound 3).
   - "density": bulk density in g/cm3 including air gaps (leafy salad 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).
   - "kcal_per_100g": energy density as served.
   - "prep": one of raw, boiled, baked, sauteed, fried, dressed.
Reply with JSON only:
{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},
 "items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>, "footprint": <number>,
            "height_cm": <number>, "density": <number>, "kcal_per_100g": <number>, "prep": "..."}]}"""

P_PRIOR = """This is an overhead photo of a single cafeteria serving on a plate or in a bowl.
Use the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).
Think about how much food is really there: many of these servings are small (a few pieces, a thin layer),
and the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.
Estimate the total weight of food you can see and its total food energy, including visible oil or sauce.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


def _obj(t, anchor=None):
    if anchor:  # last JSON after ANSWER: (reasoning chains)
        i = t.rfind("ANSWER:")
        tl = t[i:] if i >= 0 else t
        j = tl.find(anchor)
        if j < 0:
            tl, j = t, t.rfind(anchor)
        t = tl[j:]
    return json.loads(re.search(r"\{.*\}", t, re.S).group(0))

def _n(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    return d if v != v else min(max(v, lo), hi)

def _items(its, oil=0.0):
    g = sum(float(i["grams"]) for i in its)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in its)
    o = oil * sum(float(i["grams"]) for i in its if i.get("greens") is True)
    return k + o * 8.84, g + o

def _rsn(t):
    return _items(_obj(t, '{"items"')["items"])

def _den(t):
    return _items(_obj(t)["items"])

def _dn(t):
    return _items(_obj(t)["items"], OIL_FRAC)

def _geo(t):
    o = _obj(t)
    area = math.pi * (_n((o.get("vessel") or {}).get("diameter_frac"), 0.1, 1.2, 0.6) * FRAME_CM / 2) ** 2
    G = K = 0.0
    for it in o["items"]:
        if it.get("kind") == "pieces" and _n(it.get("count"), 0, 200, 0) > 0:
            g = _n(it.get("count"), 0, 200, 1) * _n(it.get("piece_g"), 0.5, 400, 30) * SHRINK
        else:
            g = (area * _n(it.get("footprint"), 0, 1, 0.1) * _n(it.get("height_cm"), 0.05, 10, 1.5)
                 * _n(it.get("density"), 0.03, 1.5, 0.8) * SHRINK)
        G += g
        K += g * _n(it.get("kcal_per_100g"), 0, 900, 150) / 100
    return K, G

def _prior(t):
    d = _obj(t)
    return float(d["kcal"]), float(d.get("mass_g") or 0)

def _gm(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None

def _view(llm, image, calls, fn):
    ks, ms = [], []
    for prompt, effort, samples in calls:
        for s in samples:  # later samples are retries on a parse failure only
            try:
                k, m = fn(llm.ask(prompt, image, model=MODEL, effort=effort, sample=s, max_tokens=8000))
            except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                continue
            if k > 0:
                ks.append(k)
                ms.append(m)
                break
    return _gm(ks), _gm(ms)

VIEWS = (
    ([(P_RSN, "low", [0, 1])], _rsn),
    ([(P_DN, "medium", [0, 10, 20])], _dn),
    ([(P_PRIOR, "low", [0]), (P_PRIOR, "low", [1]), (P_PRIOR, "low", [2])], _prior),
    ([(P_GEO, "medium", [0, 1])], _geo),
)

def estimate(image, llm):
    vs = [_view(llm, image, c, fn) for c, fn in VIEWS]
    ok = [math.log(k / REF) for k, _ in vs if k]
    if not ok:
        raise ValueError("no view parsed")
    x = [math.log(k / REF) if k else sum(ok) / len(ok) for k, _ in vs]  # failed view = mean of the others
    return {"kcal": REF * math.exp(C + WM * sum(x) / len(x)), "mass_g": _gm([m for _, m in vs])}
