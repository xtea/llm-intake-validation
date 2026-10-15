"""cal_v5: direct-total prompt with de-biasing rules (plate anchor, range-then-pick, small stays small),
one call; optional post-hoc log-linear calibration."""
import json, re, math

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a cafeteria meal. Estimate the total food energy of exactly what is visible.
Judge the amount relative to the container (dinner plate ~26 cm, side plate ~20 cm, bowl ~15 cm): how much of it is
covered and how deep the food is. Do not assume a standard serving: a few bites on a big plate is a small number
(often under 150 kcal), a heaped plate is large. First give a plausible low and high value, then your best estimate.
Reply with JSON only: {"kcal_low": <number>, "kcal_high": <number>, "kcal": <number>, "mass_g": <total grams of food>}"""
C, W, REF = 0.0, 1.0, 300.0


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    d = parse(llm.ask(PROMPT, image, model=MODEL, effort="low"))
    k = float(d["kcal"])
    return {"kcal": REF * math.exp(C + W * math.log(k / REF)), "mass_g": float(d.get("mass_g") or 0) or None}
