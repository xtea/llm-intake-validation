"""gen1 geometry v5: ensemble of three scale-reasoning decompositions of the same photo, combined by
geometric mean of kcal and mass:
  A) plate-as-ruler item grams (h2 prompt),
  B) observation-only geometry (geo_v1 prompt): vessel diameter as a fraction of the image width times a
     fixed frame width (the overhead camera height is fixed), item footprint x height x bulk density, or
     count x per-piece weight; per-piece and pile weights shrunk 15% (model priors run high),
  C) measure-then-convert item grams (geo_v3 prompt).
Geometric decompositions err differently on mass (log-error corr 0.5-0.65), so averaging cuts mass noise."""
import json, math, re

MODEL = "claude-haiku-5-5"
P_PLATE = 'This is an overhead photo of a meal on a plate or in a bowl.\nUse the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,\na cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)\nand its height, then estimate its weight in grams from that volume. Estimate only what is visible;\ndo not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.\nInclude oil, dressing or sauce as separate items when you can see them.\nReply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}'

P_GEO = 'This is an overhead photo (camera pointing straight down) of a cafeteria meal.\nDo NOT estimate grams directly. Report geometric observations only; the weight is computed from them.\n\n1. The vessel: is the food on a plate, in a bowl, or on a tray/none? Estimate the vessel\'s rim diameter as a\n   fraction of the image WIDTH (0-1), and its real diameter in cm (dinner plate ~26, side plate ~20, bowl ~15).\n2. For each distinct food item (include visible oil, butter, dressing or sauce as their own items):\n   - "kind": "pieces" if it is discrete countable units (eggs, slices, nuggets, cookies, fruit pieces, sushi),\n     otherwise "pile" (rice, salad, stew, mash, spread-out food).\n   - "count" and "piece_g" (typical weight of ONE such piece of the size you see) for pieces.\n   - "footprint": fraction of the vessel\'s area the item covers when viewed from above (0-1).\n     Be literal: a few leaves may be 0.02, a spoon of sauce 0.01, half the plate 0.5.\n   - "height_cm": average thickness/height of the item layer (a sauce smear 0.2, a slice of meat 1, a rice mound 3).\n   - "density": bulk density in g/cm3 including air gaps (leafy salad 0.1, fries 0.3, rice 0.8, meat 1.0, sauce 1.0).\n   - "kcal_per_100g": energy density as served.\n   - "prep": one of raw, boiled, baked, sauteed, fried, dressed.\nReply with JSON only:\n{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},\n "items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>, "footprint": <number>,\n            "height_cm": <number>, "density": <number>, "kcal_per_100g": <number>, "prep": "..."}]}'

P_MEASURE = 'This is an overhead photo (camera pointing straight down) of a cafeteria meal.\nWork like a surveyor. First size the vessel: plate, bowl or none, and its rim diameter in cm\n(dinner plate ~26 cm, side plate ~20 cm, small bowl ~12 cm, cereal bowl ~15 cm).\nThen for each distinct food item (include visible oil, butter, dressing or sauce as their own items) record:\n- "footprint": fraction of the vessel\'s area it covers seen from above (a few leaves 0.02, half the plate 0.5),\n- "h_cm": its average height or thickness,\n- "count": number of separate pieces (1 for a pile or spread),\n- "grams": its weight, derived from those measurements (area x height x density, or count x size of\n  each piece). Trust the measurements, not what a typical serving would weigh: a small heap is a small weight.\n- "kcal_per_100g": energy density as served (count cooking oil absorbed by fried or sauteed food).\nReply with JSON only:\n{"vessel": {"type": "plate|bowl|none", "diameter_cm": <number>},\n "items": [{"name": "...", "footprint": <number>, "h_cm": <number>, "count": <number>,\n            "grams": <number>, "kcal_per_100g": <number>}]}'

FRAME_CM = 45.0  # image width at table level (fixed rig)
PILE = 0.85
PIECE = 0.85


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


def items_sum(obs):
    g = k = 0.0
    for it in obs["items"]:
        gi = num(it.get("grams"), 0.5, 3000, 50)
        g += gi
        k += gi * num(it.get("kcal_per_100g"), 0, 900, 150) / 100
    return k, g


def geo_sum(obs):
    v = obs.get("vessel") or {}
    dcm = num(v.get("diameter_frac"), 0.1, 1.2, 0.6) * FRAME_CM
    area = math.pi * (dcm / 2) ** 2
    g = k = 0.0
    for it in obs["items"]:
        kd = num(it.get("kcal_per_100g"), 0, 900, 150) / 100
        if it.get("kind") == "pieces" and num(it.get("count"), 0, 200, 0) > 0:
            gi = num(it.get("count"), 0, 200, 1) * num(it.get("piece_g"), 0.5, 400, 30) * PIECE
        else:
            gi = (area * num(it.get("footprint"), 0, 1, 0.1) * num(it.get("height_cm"), 0.05, 10, 1.5)
                  * num(it.get("density"), 0.03, 1.5, 0.8) * PILE)
        g += gi
        k += gi * kd
    return k, g


def one(llm, image, prompt, fn):
    for s in (0, 1):
        try:
            k, g = fn(parse(llm.ask(prompt, image, model=MODEL, effort="medium", sample=s)))
            if k > 0 and g > 0:
                return k, g
        except Exception:
            pass
    return None


def estimate(image, llm):
    ests = [e for e in (one(llm, image, P_PLATE, items_sum), one(llm, image, P_GEO, geo_sum),
                        one(llm, image, P_MEASURE, items_sum)) if e]
    if not ests:
        raise ValueError("no parsable estimate")
    k = math.exp(sum(math.log(e[0]) for e in ests) / len(ests))
    g = math.exp(sum(math.log(e[1]) for e in ests) / len(ests))
    return {"kcal": k, "mass_g": g}
