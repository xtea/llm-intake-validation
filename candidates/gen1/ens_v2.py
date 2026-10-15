"""Ensemble v2 (single new view, for analysis): household-measure logging view.
Items are sized in cups / tbsp / pieces as a nutrition-app user would log them; kcal per item."""
import json, re

MODEL = "claude-haiku-5-5"
HOUSE = """This is an overhead photo of one serving of food on a plate or in a bowl (cafeteria portion).
Log it the way a careful dietitian would in a nutrition app: list each visible food item with its amount
in household measures (cups, tablespoons, slices, pieces), its weight in grams, and the kcal for that amount.
Judge the amount from what you actually see on the plate, not from a typical serving; many plates hold only
a few small items. Count visible oil, butter, dressing or sauce as their own items.
Reply with JSON only: {"items": [{"name": "...", "amount": "...", "grams": <number>, "kcal": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(HOUSE, image, model=MODEL, effort="low"))["items"]
    return {"kcal": sum(float(i["kcal"]) for i in items), "mass_g": sum(float(i["grams"]) for i in items)}
