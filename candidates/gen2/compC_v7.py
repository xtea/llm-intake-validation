"""compC_v7: 1 Haiku call (retry only on parse failure), ~$0.00015/dish: prior-anchored direct total (ens_v5 text,
low effort) + log-linear calibration.
Components:
- [invariant] direct total judged against the plate as ruler.
- [dataset] prompt prior "cafeteria serving, small 100-300 kcal, full heaped plate 700-1000 kcal" (ens_v5).
- [invariant] log-linear calibration REF*exp(C + sum w ln(x/REF)) with sum w < 1 (shrink over-dispersed totals).
- [invariant] fallback: single-view calibration (pairs) or one retry (single view) when a view fails to parse.
- [dataset] C and w fitted (Nelder-Mead, min sum|err| = mae_pct_of_mean) on the 600 search dishes of seed g2
  (search split only); confirmed on seed g2b.
"""
import json, math, re

MODEL = "claude-haiku-5-5"
REF = 300.0
FRAME_CM = 45.0
SHRINK = 0.85
P_PRIOR = 'This is an overhead photo of a single cafeteria serving on a plate or in a bowl.\nUse the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).\nThink about how much food is really there: many of these servings are small (a few pieces, a thin layer),\nand the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.\nEstimate the total weight of food you can see and its total food energy, including visible oil or sauce.\nReply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}'
TH_A = (-0.1283, 0.9824)


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    if v != v:
        return d
    return min(max(v, lo), hi)


def calib(theta, xs):
    """REF * exp(C + sum w_i ln(x_i / REF)); sum of w < 1 shrinks toward REF (undoes over-dispersed totals)."""
    return REF * math.exp(theta[0] + sum(w * math.log(max(x, 1.0) / REF) for w, x in zip(theta[1:], xs)))

def prior_view(image, llm, sample=0):
    """Prior-anchored direct total (ens_v5 text), low effort."""
    d = parse(llm.ask(P_PRIOR, image, model=MODEL, effort="low", sample=sample))
    k = float(d["kcal"])
    if k <= 0:
        raise ValueError("empty prior view")
    return k, float(d.get("mass_g") or 0)


VIEWS = (prior_view,)


def estimate(image, llm):
    vals = []
    for fn in VIEWS:
        try:
            vals.append(fn(image, llm))
        except (ValueError, KeyError, TypeError, AttributeError, IndexError):
            vals.append(None)
    a, b = (vals + [None])[:2]
    mass = (b or a or (None, None))[1] or None
    if len(VIEWS) == 1:
        if not a:  # one retry (second call) only when the single view fails to parse
            a = VIEWS[0](image, llm, sample=1)
        return {"kcal": calib(TH_A, (a[0],)), "mass_g": a[1] or None}
    if a and b:
        return {"kcal": calib(TH_AB, (a[0], b[0])), "mass_g": mass}
    if a:
        return {"kcal": calib(TH_A, (a[0],)), "mass_g": a[1] or None}
    if b:
        return {"kcal": calib(TH_B, (b[0],)), "mass_g": b[1] or None}
    raise ValueError("no view parsed")
