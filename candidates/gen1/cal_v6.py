"""cal_v6: household-measure decomposition (cups / tbsp / pieces, kcal per measure) - a different
error mode from grams x kcal/100g; optional post-hoc log-linear calibration."""
import json, re, math

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a cafeteria meal. For each visible food item, estimate how much is there in
household measures (cups, tablespoons, teaspoons, slices or pieces; 1 cup is about a fist, 1 tbsp about a thumb tip),
judging from its size relative to the plate or bowl. Then give the calories in one such measure of that food as served.
Include oil, butter, dressing or sauce as their own items when visible.
Reply with JSON only: {"items": [{"name": "...", "unit": "...", "amount": <number>, "kcal_per_unit": <number>}]}"""
C, W, REF = 0.0, 1.0, 300.0


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort="low"))["items"]
    k = sum(float(i["amount"]) * float(i["kcal_per_unit"]) for i in items)
    return {"kcal": REF * math.exp(C + W * math.log(max(k, 1.0) / REF))}
