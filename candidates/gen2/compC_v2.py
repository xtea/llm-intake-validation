"""compC_v2: 2 Haiku calls -- den_v3 item decomposition (identification + visual-fat rules) + observation-only geometry, log-linear calibration.

View A [1 call, medium effort, ~$0.00038]: den_v3 plate-ruler item list with grams + kcal/100 g -> k_A.
View B [1 call, medium effort, ~$0.00033]: geo_v1 observation prompt; grams computed in code
  (vessel diameter as fraction of image width x FRAME_CM, footprint x height x bulk density, or count x piece_g) -> k_B.
kcal = REF * exp(C + wA ln(k_A/REF) + wB ln(k_B/REF)); fallbacks: single-view calibration if one view fails.
Total ~$0.00071/dish.

Components and tags:
- [invariant] two procedures with low error correlation (log-err corr ~0.61 on search-300) averaged in log space.
- [invariant] sub-linear log-linear calibration (wA+wB ~0.83 < 1) corrects over-dispersed totals.
- [invariant] model reports observations, code does the arithmetic for view B (avoids double-counted void factors).
- [invariant] per-piece / pile weight shrink 0.85 (model priors run high; geo gen1).
- [domain] bulk-density anchors in the geometry prompt (leafy 0.1, fries 0.3, rice 0.8, meat 1.0).
- [invariant] plate-as-ruler footprint x height item weights (h2).
- [domain] misidentification rules (egg white vs feta, olives vs dates, sweet potato) + kcal/100 g references (den_v3).
- [domain] visual (not assumed) hidden-fat rule: glossy leaves get ~5% dressing.
- [dataset] FRAME_CM = 45 (fixed Nutrition5k overhead rig).
- [dataset] C, wA, wB fitted (Nelder-Mead, min sum|err|) on search-300 rows of cached gen1 views (search split only).
"""
import json, math, re

MODEL = "claude-haiku-5-5"
P_DEN = 'This is an overhead photo of a meal on a plate or in a bowl.\nUse the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,\na cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)\nand its height, then estimate its weight in grams from that volume. Estimate only what is visible;\ndo not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.\n\nThen give kcal per 100 g for each item as served:\n- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);\n  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are\n  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.\n- Fat: judge from the photo. Leaves or vegetables that look glossy, wet or coated are dressed: add a separate\n  "dressing/oil" item of about 5% of their weight at 700 kcal/100 g. Dry, matte leaves get no dressing.\n  Cooked vegetables are 25-50 unless visibly oily. Visible sauce, butter, cheese or oil: add as its own item.\n- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,\n  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,\n  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.\nReply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}'
P_GEO = 'This is an overhead photo (camera pointing straight down) of a cafeteria meal.\nDo NOT estimate grams directly. Report geometric observations only; the weight is computed from them.\n\n1. The vessel: is the food on a plate, in a bowl, or on a tray/none? Estimate the vessel\'s rim diameter as a\n   fraction of the image WIDTH (0-1), and its real diameter in cm (dinner plate ~26, side plate ~20, bowl ~15).\n2. For each distinct food item (include visible oil, butter, dressing or sauce as their own items):\n   - "kind": "pieces" if it is discrete countable units (eggs, slices, nuggets, cookies, fruit pieces, sushi),\n     otherwise "pile" (rice, salad, stew, mash, spread-out food).\n   - "count" and "piece_g" (typical weight of ONE such piece of the size you see) for pieces.\n   - "footprint": fraction of the vessel\'s area the item covers when viewed from above (0-1).\n     Be literal: a few leaves may be 0.02, a spoon of sauce 0.01, half the plate 0.5.\n   - "height_cm": average thickness/height of the item layer (a sauce smear 0.2, a slice of meat 1, a rice mound 3).\n   - "density": bulk density in g/cm3 including air gaps (leafy salad 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).\n   - "kcal_per_100g": energy density as served.\n   - "prep": one of raw, boiled, baked, sauteed, fried, dressed.\nReply with JSON only:\n{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},\n "items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>, "footprint": <number>,\n            "height_cm": <number>, "density": <number>, "kcal_per_100g": <number>, "prep": "..."}]}'
FRAME_CM = 45.0
SHRINK = 0.85
REF = 300.0
TH_AB = (-0.0686, 0.4202, 0.4077)
TH_A = (-0.0519, 0.77)
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
    items = parse(llm.ask(P_DEN, image, model=MODEL, effort="medium", sample=0))["items"]
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    if k <= 0:
        raise ValueError("empty den view")
    return k, g


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
