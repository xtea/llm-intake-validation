"""gen1 geometry v1: model reports observations only (vessel, footprint, height, density, pieces);
Python converts area -> volume -> grams. Falls back to h2-style prompt on parse failure."""
import json, math, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo (camera pointing straight down) of a cafeteria meal.
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

FALLBACK = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

FRAME_CM = None  # None: use model's vessel cm; else fixed frame width in cm
OIL = {"sauteed": 0.04, "fried": 0.06}


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


def compute(obs):
    v = obs.get("vessel") or {}
    frac = num(v.get("diameter_frac"), 0.1, 1.2, 0.6)
    dcm = num(v.get("diameter_cm"), 8, 40, 24)
    if FRAME_CM:
        dcm = frac * FRAME_CM
    area = math.pi * (dcm / 2) ** 2
    grams = kcal = 0.0
    for it in obs["items"]:
        kd = num(it.get("kcal_per_100g"), 0, 900, 150) / 100
        if it.get("kind") == "pieces" and num(it.get("count"), 0, 200, 0) > 0:
            g = num(it.get("count"), 0, 200, 1) * num(it.get("piece_g"), 0.5, 400, 30)
        else:
            g = (area * num(it.get("footprint"), 0, 1, 0.1) * num(it.get("height_cm"), 0.05, 10, 1.5)
                 * num(it.get("density"), 0.03, 1.5, 0.8))
        oil = OIL.get(str(it.get("prep", "")).lower(), 0) * g
        grams += g + oil
        kcal += g * kd + oil * 9
    return kcal, grams


def estimate(image, llm):
    for s in (0, 1):
        try:
            obs = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s))
            k, g = compute(obs)
            if k > 0:
                return {"kcal": k, "mass_g": g}
        except Exception:
            pass
    items = parse(llm.ask(FALLBACK, image, model=MODEL, effort="medium"))["items"]
    return {"kcal": sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items),
            "mass_g": sum(float(i["grams"]) for i in items)}
