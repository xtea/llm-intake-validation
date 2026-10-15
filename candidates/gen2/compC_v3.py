"""compC_v3: 2 Haiku calls (~$0.00066/dish): den_v3 item list (low) + compact arithmetic chain (low), log-linear calibration.
View A: den_v3 prompt at low effort -> k_A.  View B: rsn_v6 procedure rewritten as one terse arithmetic line per item -> k_B.
kcal = REF*exp(C + wA ln(k_A/REF) + wB ln(k_B/REF)).
FIT: provisional constants fitted on 150 g2 dishes (pilot), search split only.
Components:
- [invariant] plate-as-ruler footprint x height item weights; "small amounts get small weights" (h2/den_v3 text).
- [domain] misidentification rules (egg white vs feta, olives vs dates, orange cubes) + kcal/100 g references (den_v3).
- [domain] visual (not assumed) hidden-fat rule: glossy leaves get ~5% dressing at 700 kcal/100 g.
- [invariant] low effort for the item list (as good as medium on Haiku 5.5, 57% of the cost).
- [invariant] written arithmetic chain (vessel area -> % cover -> ml -> one bulk density -> g -> kcal), compressed to one
  line per item so it costs ~$0.00044 instead of ~$0.00088 for the prose chain (rsn_v6).
- [domain] bulk-density anchors (leafy 0.1-0.2, cut veg 0.5-0.7, grains 0.8, dense 0.9-1.0) and plate sizes.
- [invariant] log-linear calibration REF*exp(C + sum w ln(x/REF)) with sum w < 1 (shrink over-dispersed totals).
- [invariant] two procedures with low log-error correlation combined in log space (the fit chooses the weights).
- [invariant] single-view fallback calibration when one view fails to parse.
- [dataset] C and w constants fitted (Nelder-Mead, min sum|err|) on search-split rows only (see FIT note).
"""
import json, math, re

MODEL = "claude-haiku-5-5"
REF = 300.0
FRAME_CM = 45.0
SHRINK = 0.85
P_DEN = 'This is an overhead photo of a meal on a plate or in a bowl.\nUse the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,\na cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)\nand its height, then estimate its weight in grams from that volume. Estimate only what is visible;\ndo not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.\n\nThen give kcal per 100 g for each item as served:\n- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);\n  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are\n  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.\n- Fat: judge from the photo. Leaves or vegetables that look glossy, wet or coated are dressed: add a separate\n  "dressing/oil" item of about 5% of their weight at 700 kcal/100 g. Dry, matte leaves get no dressing.\n  Cooked vegetables are 25-50 unless visibly oily. Visible sauce, butter, cheese or oil: add as its own item.\n- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,\n  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,\n  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.\nReply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}'
P_ARITH = 'This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.\nWork it out in writing first, as terse arithmetic (numbers and units only, no explanations):\n\nLine 1 - Scene: what kind of meal (do not guess a total weight).\nLine 2 - Vessel: plate/bowl and its likely diameter in cm (dinner plate ~26 cm, side plate ~20 cm, cereal bowl\n~15 cm, small dish ~8 cm); area = 3.14 x (d/2)^2. Food on other plates at the edge of the photo is not part of this meal.\nThen ONE line per visible food item (include oil, dressing or sauce when you can see them):\nname: % of vessel area -> cm^2 x height cm = ml x bulk density = g x kcal/100g = kcal\nThe percents must add up to the share of the vessel actually covered by food. Height is the outer envelope of the pile.\nBulk density is the ONLY reduction factor (it already includes air and gaps), g/ml: loose leafy greens 0.1-0.2,\ncut vegetables / fruit pieces 0.5-0.7, rice / pasta / grains 0.8, mashed or dense items, meat, fish, egg, cheese,\nbread-like slices 0.9-1.0 (bread loaf ~0.3), sauces 1.0. kcal/100g is for the item as plated (cooked weight).\nLast check line: is the total plausible? Small amounts (a few leaves, a spoon of rice) get small weights; a fully\ncovered dinner plate usually holds several hundred grams. Estimate only what is visible; do not assume a typical serving.\n\nExample (generic, only to show the format and scale):\nScene: rice bowl plate with chicken and salad\nVessel: dinner plate 26 cm, 530 cm^2\ncooked rice: 30% -> 159 cm^2 x 2 = 318 ml x 0.8 = 254 g x 130 = 330 kcal\ngrilled chicken: 20% -> 106 cm^2 x 1.5 = 159 ml x 1.0 = 159 g x 165 = 262 kcal\nmixed leaves: 30% -> 159 cm^2 x 3 = 477 ml x 0.15 = 72 g x 20 = 14 kcal\ncherry tomatoes: 3% -> 16 cm^2 x 2.5 = 40 ml x 0.6 = 24 g x 18 = 4 kcal\nCheck: 85% covered dinner plate, 509 g, 610 kcal - plausible.\n\nThen, on the last line, write ANSWER: followed by JSON only, one [grams, kcal_per_100g] pair per item:\n{"items": [[<grams>, <kcal_per_100g>], ...]}\n'
TH_AB = (-0.1978, 0.416, 0.4652)
TH_A = (-0.1312, 0.8085)
TH_B = (-0.2484, 0.7375)


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

def den_view(image, llm):
    """den_v3 item list (plate ruler + identification + visual-fat rules), low effort."""
    items = parse(llm.ask(P_DEN, image, model=MODEL, effort="low"))["items"]
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    if k <= 0:
        raise ValueError("empty den view")
    return k, sum(float(i["grams"]) for i in items)


def arith_view(image, llm):
    """Compact written arithmetic chain (rsn_v6 procedure, one line per item), low effort."""
    text = llm.ask(P_ARITH, image, model=MODEL, effort="low", max_tokens=8000)
    i = text.rfind("ANSWER:")
    d = parse(text[i:] if i >= 0 else text)
    g = k = 0.0
    for it in d["items"]:
        a, b = (it["grams"], it["kcal_per_100g"]) if isinstance(it, dict) else (it[0], it[1])
        g += float(a)
        k += float(a) * float(b) / 100
    if k <= 0:
        raise ValueError("empty arith view")
    return k, g


VIEWS = (den_view, arith_view,)


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
        if not a:
            raise ValueError("no view parsed")
        return {"kcal": calib(TH_A, (a[0],)), "mass_g": a[1] or None}
    if a and b:
        return {"kcal": calib(TH_AB, (a[0], b[0])), "mass_g": mass}
    if a:
        return {"kcal": calib(TH_A, (a[0],)), "mass_g": a[1] or None}
    if b:
        return {"kcal": calib(TH_B, (b[0],)), "mass_g": b[1] or None}
    raise ValueError("no view parsed")
