"""Baseline 2: item decomposition with explicit plate-as-scale reasoning."""
import json, re

MODEL = "claude-sonnet-5-5"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium"))["items"]
    grams = sum(float(i["grams"]) for i in items)
    kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return {"kcal": kcal, "mass_g": grams}
