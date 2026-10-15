"""cal_v4: h0 direct-total prompt sampled K times (sample 0 = h0's cached call), geometric mean,
then post-hoc log-linear calibration kcal_adj = REF*exp(C + W*log(kcal/REF))."""
import json, re, math

MODEL = "claude-haiku-5-5"
PROMPT = """This is a photo of a meal. Estimate the total food energy of everything on the plate.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""
K = 5
C, W, REF = 0.0, 1.0, 300.0


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def estimate(image, llm):
    ks, ms = [], []
    for s in range(K):
        try:
            d = parse(llm.ask(PROMPT, image, model=MODEL, effort="low", sample=s))
            k, m = float(d["kcal"]), float(d.get("mass_g") or 0)
        except Exception:
            continue
        if k > 0:
            ks.append(k)
            if m > 0:
                ms.append(m)
    kcal = gmean(ks)
    return {"kcal": REF * math.exp(C + W * math.log(kcal / REF)), "mass_g": gmean(ms) if ms else None}
