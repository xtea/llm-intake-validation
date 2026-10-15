"""cal_v2: h2_plate_scale prompt sampled 3x (sample 0 = h2's cached call), median of totals.
Optional post-hoc power calibration kcal_adj = A*REF*(kcal/REF)**B (A=1, B=1 means none)."""
import json, re, statistics

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""
A, B, REF = 1.0, 1.0, 300.0
K = 3


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    tot, mass = [], []
    for s in range(K):
        try:
            items = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s))["items"]
            g = sum(float(i["grams"]) for i in items)
            k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
        except Exception:
            continue
        if k > 0:
            tot.append(k); mass.append(g)
    kcal = statistics.median(tot)
    return {"kcal": A * REF * (kcal / REF) ** B, "mass_g": statistics.median(mass)}
