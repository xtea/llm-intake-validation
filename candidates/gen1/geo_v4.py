"""gen1 geometry v4: fixed overhead rig, so the image itself is the ruler. Model reports each item's
footprint as a fraction of the whole IMAGE area (no vessel sizing), its height and density, or count x
per-piece weight for discrete pieces. Python converts with one frame-area constant."""
import json, math, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo taken by a fixed camera pointing straight down at a cafeteria tray area.
The camera height never changes, so the image frame is the ruler: the full image is about 45 cm wide and
34 cm tall (a dinner plate spans roughly 60% of the width).
Do NOT estimate grams directly. For each distinct food item (include visible oil, butter, dressing or sauce):
- "kind": "pieces" for discrete units you can count (eggs, slices, nuggets, cookies, fruit wedges, rolls),
  otherwise "pile" (rice, salad, stew, mash, sauce, scattered or spread food).
- for pieces: "count" and "piece_g" (weight of ONE piece of the size you see).
- for piles: "area_pct": percent of the WHOLE IMAGE area covered by the item seen from above
  (be literal: a few leaves 0.3, a spoon of sauce 0.2, a full dinner plate ~30),
  "h_cm": average height/thickness, "density": bulk g/cm3 including air gaps (leafy salad 0.1, fries 0.3,
  rice 0.8, meat 1.0, sauce 1.0).
- "kcal_per_100g": energy density as served.
Reply with JSON only:
{"items": [{"name": "...", "kind": "pile|pieces", "count": <number>, "piece_g": <number>,
            "area_pct": <number>, "h_cm": <number>, "density": <number>, "kcal_per_100g": <number>}]}"""

FALLBACK = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

FRAME_AREA = 45 * 34  # cm2
PILE = 1.0
PIECE = 1.0


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
    grams = kcal = 0.0
    for it in obs["items"]:
        kd = num(it.get("kcal_per_100g"), 0, 900, 150) / 100
        if it.get("kind") == "pieces" and num(it.get("count"), 0, 200, 0) > 0:
            g = num(it.get("count"), 0, 200, 1) * num(it.get("piece_g"), 0.5, 400, 30) * PIECE
        else:
            g = (FRAME_AREA * num(it.get("area_pct"), 0, 100, 3) / 100 * num(it.get("h_cm"), 0.05, 10, 1.5)
                 * num(it.get("density"), 0.03, 1.5, 0.8) * PILE)
        grams += g
        kcal += g * kd
    return kcal, grams


def estimate(image, llm):
    for s in (0, 1):
        try:
            k, g = compute(parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s)))
            if k > 0:
                return {"kcal": k, "mass_g": g}
        except Exception:
            pass
    items = parse(llm.ask(FALLBACK, image, model=MODEL, effort="medium"))["items"]
    return {"kcal": sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items),
            "mass_g": sum(float(i["grams"]) for i in items)}
