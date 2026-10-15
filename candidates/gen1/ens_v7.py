"""Ensemble v7 (single view, for analysis): item list with plate ruler plus small-serving prior."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a single cafeteria serving on a plate or in a bowl.
Use the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).
Many of these servings are small (a few pieces, a thin layer, a spoonful): a whole small serving often
weighs only 100-250 g, while a full heaped plate can weigh 500-700 g. For each food item, judge the area it
covers and its thickness, then its weight in grams; give its energy density as cooked in kcal per 100 g.
Include visible oil, butter, dressing or sauce as separate items.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort="low"))["items"]
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return {"kcal": k, "mass_g": g}
