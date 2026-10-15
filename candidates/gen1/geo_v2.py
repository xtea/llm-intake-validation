"""gen1 geometry v2: every item measured in cm (pieces x length x width x height x shape), plate as ruler;
Python converts volume -> grams. No gram or per-piece-weight priors from the model."""
import json, math, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo (camera pointing straight down) of a cafeteria meal.
Do NOT estimate weights. Measure the food with a ruler; the weight is computed from your measurements.

First measure the vessel: its rim diameter as a fraction of the image WIDTH (0-1) and in cm
(dinner plate ~26 cm, side plate ~20 cm, bowl ~15 cm; judge the size from the food and utensils on it).
Then, for each distinct food item (include visible oil, butter, dressing or sauce as their own items):
- "n": number of separate pieces of this item (1 for a single pile, mound, spread or bowl of food).
- "l_cm", "w_cm": length and width of ONE piece (or of the whole pile) seen from above, using the vessel as the ruler.
- "h_cm": its height or thickness (a sauce smear 0.2, a leaf 0.3, a slice of meat 1, a rice mound 3).
- "shape": "slab" (flat, fills its outline: slices, fillets, bread), "mound" (heap thinning to the edges:
  rice, mash, pasta, stew), "round" (balls, eggs, fruit, nuggets, rolls), "loose" (airy or scattered:
  leafy salad, fries, chips, sprinkled toppings).
- "density": density of the food itself in g/cm3 (meat 1.05, rice 0.85, bread 0.3, leafy greens 0.5, sauce 1.0, oil 0.92).
- "kcal_per_100g": energy density as served.
Small things must get small numbers: a few leaves, one slice of cucumber or a teaspoon of sauce are tiny.
Reply with JSON only:
{"vessel": {"type": "plate|bowl|none", "diameter_frac": <number>, "diameter_cm": <number>},
 "items": [{"name": "...", "n": <number>, "l_cm": <number>, "w_cm": <number>, "h_cm": <number>,
            "shape": "...", "density": <number>, "kcal_per_100g": <number>}]}"""

FALLBACK = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

# fraction of the bounding box (l x w x h) actually filled by food
SHAPE = {"slab": 0.75, "mound": 0.4, "round": 0.52, "loose": 0.25}
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
    grams = kcal = 0.0
    for it in obs["items"]:
        kd = num(it.get("kcal_per_100g"), 0, 900, 150) / 100
        vol = (num(it.get("n"), 1, 100, 1) * num(it.get("l_cm"), 0.2, 40, 5) * num(it.get("w_cm"), 0.2, 40, 5)
               * num(it.get("h_cm"), 0.05, 12, 1) * SHAPE.get(str(it.get("shape", "")).lower(), 0.5))
        g = vol * num(it.get("density"), 0.05, 1.5, 0.9) * SCALE
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
