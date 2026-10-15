"""compC_v5 (gen2 composer C, best accuracy per dollar): 2 Haiku calls, ~$0.00054/dish.
View A: den_v3 item list (grams x kcal/100 g) at LOW effort -> k_A (~$0.00022).
View B: geo_v1 observation-only geometry at medium effort, grams computed in code -> k_B (~$0.00033).
kcal = REF*exp(C + wA ln(k_A/REF) + wB ln(k_B/REF)); log-error corr(A,B) ~0.63 on g2.
Components:
- [invariant] plate-as-ruler footprint x height item weights; "small amounts get small weights" (h2/den_v3 text).
- [domain] misidentification rules (egg white vs feta, olives vs dates, orange cubes) + kcal/100 g references (den_v3).
- [domain] visual (not assumed) hidden-fat rule: glossy leaves get ~5% dressing at 700 kcal/100 g.
- [invariant] low effort for the item list (as good as medium on Haiku 5.5, ~57% of the cost).
- [invariant] model reports observations only, code does the arithmetic; per-piece/pile shrink 0.85 (priors run high).
- [domain] bulk-density anchors in the geometry prompt (leafy 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).
- [dataset] FRAME_CM = 45: fixed Nutrition5k overhead rig (image width at table level).
- [invariant] two procedures with low log-error correlation combined in log space (the fit chooses the weights).
- [invariant] log-linear calibration REF*exp(C + sum w ln(x/REF)) with sum w < 1 (shrink over-dispersed totals).
- [invariant] fallback: single-view calibration (pairs) or one retry (single view) when a view fails to parse.
- [dataset] C and w fitted (Nelder-Mead, min sum|err| = mae_pct_of_mean) on the 600 search dishes of seed g2
  (search split only); confirmed on seed g2b.
"""
import json, math, re

MODEL = "claude-haiku-5-5"
REF = 300.0
FRAME_CM = 45.0
SHRINK = 0.85
P_DEN = 'This is an overhead photo of a meal on a plate or in a bowl.\nUse the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,\na cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)\nand its height, then estimate its weight in grams from that volume. Estimate only what is visible;\ndo not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.\n\nThen give kcal per 100 g for each item as served:\n- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);\n  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are\n  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.\n- Fat: judge from the photo. Leaves or vegetables that look glossy, wet or coated are dressed: add a separate\n  "dressing/oil" item of about 5% of their weight at 700 kcal/100 g. Dry, matte leaves get no dressing.\n  Cooked vegetables are 25-50 unless visibly oily. Visible sauce, butter, cheese or oil: add as its own item.\n- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,\n  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,\n  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.\nReply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}'
P_GEO = 'This is an overhead photo (camera pointing straight down) of a cafeteria meal.\nDo NOT estimate grams directly. Report geometric observations only; the weight is computed from them.\n\n1. The vessel: is the food on a plate, in a bowl, or on a tray/none? Estimate the vessel\'s rim diameter as a\n   fraction of the image WIDTH (0-1), and its real diameter in cm (dinner plate ~26, side plate ~20, bowl ~15).\n2. For each distinct food item (include visible oil, butter, dressing or sauce as their own items):\n   - "kind": "pieces" if it is discrete countable units (eggs, slices, nuggets, cookies, fruit pieces, sushi),\n     otherwise "pile" (rice, salad, stew, mash, spread-out food).\n   - "count" and "piece_g" (typical weight of ONE such piece of the size you see) for pieces.\n   - "footprint": fraction of the vessel\'s area the item covers when viewed from above (0-1).\n     Be literal: a few leaves may be 0.02, a spoon of sauce 0.01, half the plate 0.5.\n   - "height_cm": average thickness/height of the item layer (a sauce smear 0.2, a slice of meat 1, a rice mound 3).\n   - "density": bulk density in g/cm3 including air gaps (leafy salad 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).\n   - "kcal_per_100g": energy density as served.\n   - "prep": one of raw, boiled, baked, sauteed, fried, dressed.\nReply with JSON only:\n{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},\n "items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>, "footprint": <number>,\n            "height_cm": <number>, "density": <number>, "kcal_per_100g": <number>, "prep": "..."}]}'
TH_AB = (-0.1204, 0.4923, 0.3686)
TH_A = (-0.1576, 0.8416)
TH_B = (-0.1085, 0.7185)


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


def calib(theta, xs):
    """REF * exp(C + sum w_i ln(x_i / REF)); sum of w < 1 shrinks toward REF (undoes over-dispersed totals)."""
    return REF * math.exp(theta[0] + sum(w * math.log(max(x, 1.0) / REF) for w, x in zip(theta[1:], xs)))

def den_view(image, llm, sample=0):
    """den_v3 item list (plate ruler + identification + visual-fat rules), low effort."""
    items = parse(llm.ask(P_DEN, image, model=MODEL, effort="low", sample=sample))["items"]
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    if k <= 0:
        raise ValueError("empty den view")
    return k, sum(float(i["grams"]) for i in items)


def geo_view(image, llm):
    """Observation-only geometry (geo_v1): grams computed in code from the fixed frame width, medium effort."""
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


VIEWS = (den_view, geo_view,)


def estimate(image, llm):
    vals = []
    for fn in VIEWS:
        try:
            vals.append(fn(image, llm))
        except (ValueError, KeyError, TypeError, AttributeError, IndexError):
            vals.append(None)
    a, b = (vals + [None])[:2]
    mass = (b or a or (None, None))[1] or None
    if len(VIEWS) == 1:
        if not a:  # one retry (second call) only when the single view fails to parse
            a = VIEWS[0](image, llm, sample=1)
        return {"kcal": calib(TH_A, (a[0],)), "mass_g": a[1] or None}
    if a and b:
        return {"kcal": calib(TH_AB, (a[0], b[0])), "mass_g": mass}
    if a:
        return {"kcal": calib(TH_A, (a[0],)), "mass_g": a[1] or None}
    if b:
        return {"kcal": calib(TH_B, (b[0],)), "mass_g": b[1] or None}
    raise ValueError("no view parsed")
