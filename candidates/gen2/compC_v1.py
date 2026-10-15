"""compC_v1: 2 Haiku calls -- cheap prior-anchored direct total + observation-only geometry, log-linear calibration.

View A [1 call, low effort, ~$0.00015]: PRIOR direct-total prompt (ens_v5/ens_v10 text, sample 0) -> k_A.
View B [1 call, medium effort, ~$0.00033]: geo_v1 observation prompt; grams computed in code
  (vessel diameter as fraction of image width x FRAME_CM, footprint x height x bulk density, or count x piece_g) -> k_B.
kcal = REF * exp(C + wA ln(k_A/REF) + wB ln(k_B/REF)); fallbacks: single-view calibration if one view fails.
Total ~$0.00048/dish.

Components and tags:
- [invariant] two procedures with low error correlation (log-err corr ~0.56 on search-300) averaged in log space.
- [invariant] sub-linear log-linear calibration (wA+wB ~0.94 < 1) corrects over-dispersed totals.
- [invariant] model reports observations, code does the arithmetic for view B (avoids double-counted void factors).
- [invariant] per-piece / pile weight shrink 0.85 (model priors run high; geo gen1).
- [domain] bulk-density anchors in the geometry prompt (leafy 0.1, fries 0.3, rice 0.8, meat 1.0).
- [dataset] PRIOR prompt text "cafeteria serving, small 100-300 kcal, full plate 700-1000 kcal".
- [dataset] FRAME_CM = 45 (fixed Nutrition5k overhead rig).
- [dataset] C, wA, wB fitted (Nelder-Mead, min sum|err|) on search-300 rows of cached gen1 views (search split only).
"""
import json, math, re

MODEL = "claude-haiku-5-5"
P_PRIOR = 'This is an overhead photo of a single cafeteria serving on a plate or in a bowl.\nUse the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).\nThink about how much food is really there: many of these servings are small (a few pieces, a thin layer),\nand the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.\nEstimate the total weight of food you can see and its total food energy, including visible oil or sauce.\nReply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}'
P_GEO = 'This is an overhead photo (camera pointing straight down) of a cafeteria meal.\nDo NOT estimate grams directly. Report geometric observations only; the weight is computed from them.\n\n1. The vessel: is the food on a plate, in a bowl, or on a tray/none? Estimate the vessel\'s rim diameter as a\n   fraction of the image WIDTH (0-1), and its real diameter in cm (dinner plate ~26, side plate ~20, bowl ~15).\n2. For each distinct food item (include visible oil, butter, dressing or sauce as their own items):\n   - "kind": "pieces" if it is discrete countable units (eggs, slices, nuggets, cookies, fruit pieces, sushi),\n     otherwise "pile" (rice, salad, stew, mash, spread-out food).\n   - "count" and "piece_g" (typical weight of ONE such piece of the size you see) for pieces.\n   - "footprint": fraction of the vessel\'s area the item covers when viewed from above (0-1).\n     Be literal: a few leaves may be 0.02, a spoon of sauce 0.01, half the plate 0.5.\n   - "height_cm": average thickness/height of the item layer (a sauce smear 0.2, a slice of meat 1, a rice mound 3).\n   - "density": bulk density in g/cm3 including air gaps (leafy salad 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).\n   - "kcal_per_100g": energy density as served.\n   - "prep": one of raw, boiled, baked, sauteed, fried, dressed.\nReply with JSON only:\n{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},\n "items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>, "footprint": <number>,\n            "height_cm": <number>, "density": <number>, "kcal_per_100g": <number>, "prep": "..."}]}'
FRAME_CM = 45.0
SHRINK = 0.85
REF = 300.0
TH_AB = (-0.1126, 0.6032, 0.3389)
TH_A = (-0.1512, 0.9672)
TH_B = (-0.115, 0.6547)


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    if v != v:
        return d
    return min(max(v, lo), hi)


def geo_view(image, llm):
    """Observation-only geometry (geo_v1/geo_v5 view B): grams computed in code from the fixed frame width."""
    obs = parse(llm.ask(P_GEO, image, model=MODEL, effort="medium"))
    v = obs.get("vessel") or {}
    dcm = num(v.get("diameter_frac"), 0.1, 1.2, 0.6) * FRAME_CM
    area = math.pi * (dcm / 2) ** 2
    g = k = 0.0
    for it in obs["items"]:
        kd = num(it.get("kcal_per_100g"), 0, 900, 150) / 100
        if it.get("kind") == "pieces" and num(it.get("count"), 0, 200, 0) > 0:
            gi = num(it.get("count"), 0, 200, 1) * num(it.get("piece_g"), 0.5, 400, 30) * SHRINK
        else:
            gi = (area * num(it.get("footprint"), 0, 1, 0.1) * num(it.get("height_cm"), 0.05, 10, 1.5)
                  * num(it.get("density"), 0.03, 1.5, 0.8) * SHRINK)
        g += gi
        k += gi * kd
    if k <= 0:
        raise ValueError("empty geo view")
    return k, g


def calib(theta, xs):
    """Log-linear calibration: REF * exp(C + sum w_i ln(x_i / REF)). Sum of w < 1 = shrink toward REF."""
    return REF * math.exp(theta[0] + sum(w * math.log(max(x, 1.0) / REF) for w, x in zip(theta[1:], xs)))


def prior_view(image, llm):
    d = parse(llm.ask(P_PRIOR, image, model=MODEL, effort="low", sample=0))
    k = float(d["kcal"])
    if k <= 0:
        raise ValueError("empty prior view")
    return k, float(d.get("mass_g") or 0)


def estimate(image, llm):
    try:
        ka, ga = prior_view(image, llm)
    except (ValueError, KeyError, TypeError, AttributeError):
        ka = ga = None
    try:
        kb, gb = geo_view(image, llm)
    except (ValueError, KeyError, TypeError, AttributeError):
        kb = gb = None
    if ka and kb:
        return {"kcal": calib(TH_AB, (ka, kb)), "mass_g": gb}
    if ka:
        return {"kcal": calib(TH_A, (ka,)), "mass_g": ga or None}
    if kb:
        return {"kcal": calib(TH_B, (kb,)), "mass_g": gb}
    raise ValueError("no view parsed")
