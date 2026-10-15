"""Baseline 1: list items with grams and kcal per 100 g, then sum in code."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is a photo of a meal. List every food item you can see.
For each item give its estimated weight in grams and its energy density in kcal per 100 g
(include cooking oil, dressing or sauce as their own items when visible).
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort="low"))["items"]
    grams = sum(float(i["grams"]) for i in items)
    kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return {"kcal": kcal, "mass_g": grams}
