"""gen1 geometry v3: model first records geometry per item (vessel size, footprint, height, count), then
converts it to grams itself; Python combines model grams with its own geometric grams (geometric mean)."""
import json, math, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo (camera pointing straight down) of a cafeteria meal.
Work like a surveyor. First size the vessel: plate, bowl or none, and its rim diameter in cm
(dinner plate ~26 cm, side plate ~20 cm, small bowl ~12 cm, cereal bowl ~15 cm).
Then for each distinct food item (include visible oil, butter, dressing or sauce as their own items) record:
- "footprint": fraction of the vessel's area it covers seen from above (a few leaves 0.02, half the plate 0.5),
- "h_cm": its average height or thickness,
- "count": number of separate pieces (1 for a pile or spread),
- "grams": its weight, derived from those measurements (area x height x density, or count x size of
  each piece). Trust the measurements, not what a typical serving would weigh: a small heap is a small weight.
- "kcal_per_100g": energy density as served (count cooking oil absorbed by fried or sauteed food).
Reply with JSON only:
{"vessel": {"type": "plate|bowl|none", "diameter_cm": <number>},
 "items": [{"name": "...", "footprint": <number>, "h_cm": <number>, "count": <number>,
            "grams": <number>, "kcal_per_100g": <number>}]}"""

FALLBACK = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

W_GEO = 0.0     # weight of Python geometric grams vs model grams (log space)
FILL = 0.5      # fraction of footprint x height box filled by food, times density
SCALE = 1.0


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
    dcm = num((obs.get("vessel") or {}).get("diameter_cm"), 8, 40, 24)
    area = math.pi * (dcm / 2) ** 2
    grams = kcal = 0.0
    for it in obs["items"]:
        kd = num(it.get("kcal_per_100g"), 0, 900, 150) / 100
        gm = num(it.get("grams"), 0.5, 3000, 50)
        gg = max(area * num(it.get("footprint"), 0, 1, 0.1) * num(it.get("h_cm"), 0.05, 12, 1) * FILL, 0.5)
        g = math.exp(W_GEO * math.log(gg) + (1 - W_GEO) * math.log(gm)) * SCALE
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
