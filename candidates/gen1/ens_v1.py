"""Ensemble v1: geometric mean of two views (direct total @low + plate-scale item list @medium),
then one global calibration scalar (fit on search; both views overestimate on average)."""
import json, math, re

MODEL = "claude-haiku-5-5"
CAL = 0.77

DIRECT = """This is a photo of a meal. Estimate the total food energy of everything on the plate.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""

PLATE = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def view_direct(image, llm):
    d = parse(llm.ask(DIRECT, image, model=MODEL, effort="low"))
    return float(d["kcal"]), float(d.get("mass_g") or 0)


def view_plate(image, llm):
    items = parse(llm.ask(PLATE, image, model=MODEL, effort="medium"))["items"]
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return k, g


def geo(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def estimate(image, llm):
    views = []
    for f in (view_direct, view_plate):
        try:
            views.append(f(image, llm))
        except Exception:
            pass
    if not views:
        raise ValueError("no view parsed")
    return {"kcal": CAL * geo([k for k, _ in views]), "mass_g": geo([g for _, g in views])}
