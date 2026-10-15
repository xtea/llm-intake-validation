"""Baseline 3: b1 sampled 3 times, median of totals."""
import json, re, statistics

MODEL = "claude-sonnet-5-5"
PROMPT = """This is a photo of a meal. List every food item you can see.
For each item give its estimated weight in grams and its energy density in kcal per 100 g
(include cooking oil, dressing or sauce as their own items when visible).
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    tot, mass = [], []
    for s in range(3):
        items = parse(llm.ask(PROMPT, image, model=MODEL, effort="low", sample=s))["items"]
        mass.append(sum(float(i["grams"]) for i in items))
        tot.append(sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items))
    return {"kcal": statistics.median(tot), "mass_g": statistics.median(mass)}
