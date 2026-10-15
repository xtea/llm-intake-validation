"""Ensemble v3 (single view, for analysis): self-critique of the plate-scale item list.
Call 1 = h2 plate-scale prompt (cached); call 2 shows the model its own list and asks it to audit it."""
import json, re

MODEL = "claude-haiku-5-5"
PLATE = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

CRITIQUE = """This is an overhead photo of a meal. A first-pass estimate listed these items:
{items}
Audit this list against the photo, item by item:
- Is the item really there and correctly identified (e.g. not confusing cauliflower with potato, or water-rich
  vegetables with starch)? Remove or rename wrong items; add clearly visible items that were missed.
- Is the weight plausible for the area it covers on the plate and its thickness? A thin layer or a few pieces
  weighs little; a deep mound weighs much more. Fix weights that are off by more than about 25%.
- Is the kcal per 100 g right for the food as cooked (plain steamed vegetables are 20-40, cooked grains 110-160,
  meats 150-280, cheese 350-400, nuts 550-650, oil 884)?
Reply with JSON only, the corrected full list: {{"items": [{{"name": "...", "grams": <number>, "kcal_per_100g": <number>}}]}}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def tot(items):
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return k, g


def estimate(image, llm):
    items = parse(llm.ask(PLATE, image, model=MODEL, effort="medium"))["items"]
    k0, g0 = tot(items)
    try:
        lst = json.dumps([{"name": i["name"], "grams": round(float(i["grams"])),
                           "kcal_per_100g": round(float(i["kcal_per_100g"]))} for i in items])
        k1, g1 = tot(parse(llm.ask(CRITIQUE.format(items=lst), image, model=MODEL, effort="low"))["items"])
        if k1 > 0:
            return {"kcal": k1, "mass_g": g1}
    except Exception:
        pass
    return {"kcal": k0, "mass_g": g0}
