"""H_v2 (gen3 mutator H, aggregation): compA_v4's three views + geometry view G joining the average ONLY when
it reads above the consensus (one-sided), then compA's 2-constant power law.
Components (tag):
  view R  [invariant] rsn_v6 written plate-ruler procedure, 2 chains (medium s0, low s0), geo-mean. = compA_v4.
  view DN [domain]+[dataset] den_v4 identification/density rules + greens oil OIL_FRAC 0.09 [dataset]. = compA_v4.
  view P  [dataset] ens_v5 cafeteria-prior direct total, 3 samples (low s0..s2), geo-mean. = compA_v4.
  view G  [invariant]+[dataset] geo_v1 observation-only geometry (medium s0), grams in code from FRAME_CM=45 [dataset]
          (fixed Nutrition5k rig) and SHRINK 0.85. Byte-identical prompt to geo_v1 / compC_v5 (cached).
  combiner [invariant] z = mean of available log(R, DN, P); if log G > z + TAU, G joins the mean (weight 1/4).
          Why: every view compresses the top (truth/estimate slope < 1); G has the highest mass slope (0.90 vs P 0.66)
          and is closest to truth on the worst under-reads. G always-in: g3 cv -0.54, g3b-unseen +0.04 vs compA
          (gate minus always-in on unseen -0.34 [-0.64,-0.04]); median/trim/outlier-drop hurt. TAU=0.2 (third constant, best of {0,0.2,0.4,0.6} on g3 cv).
  calibration [dataset] kcal = REF*exp(C + W*z); C, W fitted (min sum|err|) on search --n 600 --seed g3 only.
  Fitted: C=-0.1032, W=0.98. g3 in-sample 30.54; g3 5-fold x20 cv 30.74 (compA_v4 views refit: 31.27).
  Evidence (paired vs compA rule, bootstrap 90% CI): O (399-451 search dishes outside g3/g3b) -0.26 [-0.66,+0.15]; g3 cv -0.55 [-0.95,-0.13]; g3b-unseen
  (380, constants from g3) -0.50 [-1.01,+0.02].
  Cost ~3.0 m$/dish (8 Haiku calls; compA_v4 2.7).
"""
import json, re, math

MODEL = "claude-haiku-5-5"
REF = 300.0
OIL_FRAC = 0.09
FRAME_CM = 45.0
C = -0.1032
W = 0.98
TAU = 0.2
_HEAD = 'This is an overhead photo of a meal on a plate or in a bowl.\nUse the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,\na cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)\nand its height, then estimate its weight in grams from that volume. Estimate only what is visible;\ndo not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.\n\n'
_MID = 'Then give kcal per 100 g for each item as served:\n- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);\n  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are\n  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.\n- Fat: '
_REFS = '- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,\n  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,\n  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.\n'
_TJ = 'Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>'
P_RSN = 'This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.\nWork through these steps in writing, briefly, before giving the answer.\n\nSTEP 1 - Scene: what kind of meal is this? (Do not guess a total weight yet.)\nSTEP 2 - Vessel: identify the plate/bowl and its likely diameter in cm (dinner plate ~26 cm, side plate\n~20 cm, cereal bowl ~15 cm, small dish ~8 cm). Vessel area = 3.14 x (diameter/2)^2. Food on other\nplates at the edge of the photo is not part of this meal.\nSTEP 3 - Items: list every distinct visible food, including oil, dressing or sauce when you can see them.\nSTEP 4 - Area: for each item, the percent of the vessel area it covers. These percents must add up to the\nshare of the vessel actually covered by food (check this; if food covers most of the plate they should\nadd up to most of 100%).\nSTEP 5 - Volume: area (cm^2) x typical height (cm) = gross volume in ml, measured as the outer envelope\nof the pile. Do not reduce it here.\nSTEP 6 - Grams: gross volume x bulk density. The bulk density already accounts for air and gaps, so this\nis the ONLY reduction factor - do not apply any other gap or airy factor. Typical bulk densities (g/ml):\nloose leafy greens 0.1-0.2, cut vegetables / fruit pieces 0.5-0.7, rice / pasta / grains 0.8,\nmashed or dense items, meat, fish, egg, cheese, bread-like slices 0.9-1.0 (bread loaf ~0.3), sauces 1.0.\nSTEP 7 - Energy: kcal per 100 g for each item as plated (cooked weight); multiply.\nSTEP 8 - Sanity check: is the total plausible for what is visible? Small amounts (a few leaves, a spoon of\nrice) must get small weights; a fully covered dinner plate usually holds several hundred grams.\nEstimate only what is visible; do not assume a typical serving.\n\nTwo worked examples (generic, only to show the arithmetic and the range of scales):\n\nExample A (small): side plate 20 cm, area 314 cm^2, food covers ~15%. Cherry tomatoes 6% = 19 cm^2 x 2.5 cm\n= 47 ml x 0.6 = 28 g x 18 kcal/100g = 5 kcal. Cheese slice 9% = 28 cm^2 x 0.3 cm = 8 ml x 1.0 = 8 g\nx 400 kcal/100g = 32 kcal. Total 36 g, 37 kcal.\n\nExample B (large): dinner plate 26 cm, area 530 cm^2, food covers ~85%. Cooked rice 30% = 159 cm^2 x 2 cm\n= 318 ml x 0.8 = 254 g x 130 = 330 kcal. Grilled chicken pieces 20% = 106 cm^2 x 1.5 cm = 159 ml x 1.0\n= 159 g x 165 = 262 kcal. Mixed leaves 30% = 159 cm^2 x 3 cm = 477 ml x 0.15 = 72 g x 20 = 14 kcal.\nRoasted vegetables 5% = 27 cm^2 x 2 cm = 53 ml x 0.6 = 32 g x 60 = 19 kcal. Oil sheen ~5 g x 880 = 44 kcal.\nTotal 522 g, 669 kcal.\n\nThen, on the last line, write ANSWER: followed by JSON only:\n{"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}'
P_DN = _HEAD + _MID + 'raw leafy greens (lettuce, mixed greens, arugula, spinach, kale, chard) get "greens": true; their\n  dressing is added automatically, so do not list a dressing for them. Cooked vegetables are 25-50 and get no\n  oil item unless oil is visibly pooled. Other visible sauce, butter, cheese or oil: add as its own item.\n' + _REFS + _TJ + ', "greens": <true|false>}]}'
P_PRIOR = 'This is an overhead photo of a single cafeteria serving on a plate or in a bowl.\nUse the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).\nThink about how much food is really there: many of these servings are small (a few pieces, a thin layer),\nand the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.\nEstimate the total weight of food you can see and its total food energy, including visible oil or sauce.\nReply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}'
P_GEO = 'This is an overhead photo (camera pointing straight down) of a cafeteria meal.\nDo NOT estimate grams directly. Report geometric observations only; the weight is computed from them.\n\n1. The vessel: is the food on a plate, in a bowl, or on a tray/none? Estimate the vessel\'s rim diameter as a\n   fraction of the image WIDTH (0-1), and its real diameter in cm (dinner plate ~26, side plate ~20, bowl ~15).\n2. For each distinct food item (include visible oil, butter, dressing or sauce as their own items):\n   - "kind": "pieces" if it is discrete countable units (eggs, slices, nuggets, cookies, fruit pieces, sushi),\n     otherwise "pile" (rice, salad, stew, mash, spread-out food).\n   - "count" and "piece_g" (typical weight of ONE such piece of the size you see) for pieces.\n   - "footprint": fraction of the vessel\'s area the item covers when viewed from above (0-1).\n     Be literal: a few leaves may be 0.02, a spoon of sauce 0.01, half the plate 0.5.\n   - "height_cm": average thickness/height of the item layer (a sauce smear 0.2, a slice of meat 1, a rice mound 3).\n   - "density": bulk density in g/cm3 including air gaps (leafy salad 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).\n   - "kcal_per_100g": energy density as served.\n   - "prep": one of raw, boiled, baked, sauteed, fried, dressed.\nReply with JSON only:\n{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},\n "items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>, "footprint": <number>,\n            "height_cm": <number>, "density": <number>, "kcal_per_100g": <number>, "prep": "..."}]}'


def _json(text, anchor=None):
    if anchor:
        i = text.rfind("ANSWER:")
        tail = text[i:] if i >= 0 else text
        j = tail.find(anchor)
        if j < 0:
            tail, j = text, text.rfind(anchor)
        text = tail[max(j, 0):]
    return json.loads(re.search(r"\{.*\}", text, re.S).group(0))


def _sum(items, oil=0.0):
    g = k = gg = 0.0
    for it in items:
        a, b = (it["grams"], it["kcal_per_100g"]) if isinstance(it, dict) else (it[0], it[1])
        g += float(a)
        k += float(a) * float(b) / 100
        if isinstance(it, dict) and it.get("greens") is True:
            gg += float(a)
    return k + oil * gg * 8.84, g + oil * gg


def _rsn(t):
    return _sum(_json(t, '{"items"')["items"])


def _plain(t):
    return _sum(_json(t)["items"])


def _dn(t):
    return _sum(_json(t)["items"], OIL_FRAC)


def _top(t):
    d = _json(t)
    return float(d["kcal"]), float(d.get("mass_g") or 0)


def _num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    return d if v != v else min(max(v, lo), hi)


def _geo(t):
    obs = _json(t)
    area = math.pi * (_num((obs.get("vessel") or {}).get("diameter_frac"), 0.1, 1.2, 0.6) * FRAME_CM / 2) ** 2
    g = k = 0.0
    for it in obs["items"]:
        if it.get("kind") == "pieces" and _num(it.get("count"), 0, 200, 0) > 0:
            gi = _num(it.get("count"), 0, 200, 1) * _num(it.get("piece_g"), 0.5, 400, 30) * 0.85
        else:
            gi = (area * _num(it.get("footprint"), 0, 1, 0.1) * _num(it.get("height_cm"), 0.05, 10, 1.5)
                  * _num(it.get("density"), 0.03, 1.5, 0.8) * 0.85)
        g += gi
        k += gi * _num(it.get("kcal_per_100g"), 0, 900, 150) / 100
    return k, g


UNITS = [[(P_RSN, "medium", [0], _rsn), (P_RSN, "low", [0], _rsn)], [(P_DN, "medium", [0, 10, 20], _dn)], [(P_PRIOR, "low", [0], _top), (P_PRIOR, "low", [1], _top), (P_PRIOR, "low", [2], _top)], [(P_GEO, "medium", [0], _geo)]]


def _gm(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def _unit(llm, image, calls):
    ks, ms = [], []
    for prompt, effort, samples, fn in calls:
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
    vals = [_unit(llm, image, u) for u in UNITS]
    base = [math.log(k / REF) for k, _ in vals[:3] if k]
    g = math.log(vals[3][0] / REF) if vals[3][0] else None
    if not base and g is None:
        raise ValueError("no view parsed")
    z = sum(base) / len(base) if base else g
    if base and g is not None and g > z + TAU:
        z = (sum(base) + g) / (len(base) + 1)
    return {"kcal": REF * math.exp(C + W * z), "mass_g": _gm([m for _, m in vals])}
