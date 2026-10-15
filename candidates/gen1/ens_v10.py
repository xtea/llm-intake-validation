"""Ensemble v10: geometric mean of three cheap direct-total views, then one global calibration scalar.
  view A: plain direct total (h0 prompt, low effort, sample 0)
  view B/C: direct total with plate ruler + small-serving prior (ens_v5 prompt, low effort, samples 0 and 1)
The two prompts make partly independent errors (log-error corr ~0.81); the two samples of B add
resampling noise reduction (corr ~0.92). CAL fit on search (all views overestimate)."""
import json, math, re

MODEL = "claude-haiku-5-5"
CAL = 0.82
N_PRIOR_SAMPLES = 2

DIRECT = """This is a photo of a meal. Estimate the total food energy of everything on the plate.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""

PRIOR = """This is an overhead photo of a single cafeteria serving on a plate or in a bowl.
Use the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).
Think about how much food is really there: many of these servings are small (a few pieces, a thin layer),
and the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.
Estimate the total weight of food you can see and its total food energy, including visible oil or sauce.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    d = json.loads(m.group(0))
    return float(d["kcal"]), float(d.get("mass_g") or 0)


def geo(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else 0.0


def estimate(image, llm):
    calls = [(DIRECT, 0)] + [(PRIOR, s) for s in range(N_PRIOR_SAMPLES)]
    views = []
    for prompt, s in calls:
        try:
            k, g = parse(llm.ask(prompt, image, model=MODEL, effort="low", sample=s))
            if k > 0:
                views.append((k, g))
        except Exception:
            pass
    if not views:
        raise ValueError("no view parsed")
    return {"kcal": CAL * geo([k for k, _ in views]), "mass_g": geo([g for _, g in views])}
