"""F_v1: compA_v4 views R, DN, P (byte-identical prompts) + view B; equal-weight geometric mean + 2-constant power law.

  R  [invariant] rsn_v6 written chain x2.
  DN [domain]+[dataset] den_v4 rules + greens oil.
  P  [dataset] cafeteria-prior direct total x3.
  B  [invariant] blind two-stage density. Stage 1 (image): plate-ruler grams + purely visual description per
     item, the food is NOT named. Stage 2, two TEXT-ONLY calls: B2 = 2-4 candidate foods with probabilities and
     kcal/100 g, item density = exp(E[ln kcal/100g]); BM = expected water/protein/fat/carb -> Atwater 4/4/9.
     View density = GM of both; kcal = grams x density.
  calibration [dataset] kcal = REF*exp(C + WM*mean ln(v/REF)) over USE; Nelder-Mead on search --n 600 --seed g3.
  Fitted C=-0.1358 WM=0.9632: g3 31.68 (compA_v4 refit 31.82); g3b-unseen(380) 31.76 vs compA_v4 31.39 -> no gain.
"""
import json, re, math

MODEL = "claude-haiku-5-5"
REF = 300.0
OIL_FRAC = 0.09

USE = ("R", "DN", "P", "B")
C = -0.1358
WM = 0.9632

P_RSN = """This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.
Work through these steps in writing, briefly, before giving the answer.

STEP 1 - Scene: what kind of meal is this? (Do not guess a total weight yet.)
STEP 2 - Vessel: identify the plate/bowl and its likely diameter in cm (dinner plate ~26 cm, side plate
~20 cm, cereal bowl ~15 cm, small dish ~8 cm). Vessel area = 3.14 x (diameter/2)^2. Food on other
plates at the edge of the photo is not part of this meal.
STEP 3 - Items: list every distinct visible food, including oil, dressing or sauce when you can see them.
STEP 4 - Area: for each item, the percent of the vessel area it covers. These percents must add up to the
share of the vessel actually covered by food (check this; if food covers most of the plate they should
add up to most of 100%).
STEP 5 - Volume: area (cm^2) x typical height (cm) = gross volume in ml, measured as the outer envelope
of the pile. Do not reduce it here.
STEP 6 - Grams: gross volume x bulk density. The bulk density already accounts for air and gaps, so this
is the ONLY reduction factor - do not apply any other gap or airy factor. Typical bulk densities (g/ml):
loose leafy greens 0.1-0.2, cut vegetables / fruit pieces 0.5-0.7, rice / pasta / grains 0.8,
mashed or dense items, meat, fish, egg, cheese, bread-like slices 0.9-1.0 (bread loaf ~0.3), sauces 1.0.
STEP 7 - Energy: kcal per 100 g for each item as plated (cooked weight); multiply.
STEP 8 - Sanity check: is the total plausible for what is visible? Small amounts (a few leaves, a spoon of
rice) must get small weights; a fully covered dinner plate usually holds several hundred grams.
Estimate only what is visible; do not assume a typical serving.

Two worked examples (generic, only to show the arithmetic and the range of scales):

Example A (small): side plate 20 cm, area 314 cm^2, food covers ~15%. Cherry tomatoes 6% = 19 cm^2 x 2.5 cm
= 47 ml x 0.6 = 28 g x 18 kcal/100g = 5 kcal. Cheese slice 9% = 28 cm^2 x 0.3 cm = 8 ml x 1.0 = 8 g
x 400 kcal/100g = 32 kcal. Total 36 g, 37 kcal.

Example B (large): dinner plate 26 cm, area 530 cm^2, food covers ~85%. Cooked rice 30% = 159 cm^2 x 2 cm
= 318 ml x 0.8 = 254 g x 130 = 330 kcal. Grilled chicken pieces 20% = 106 cm^2 x 1.5 cm = 159 ml x 1.0
= 159 g x 165 = 262 kcal. Mixed leaves 30% = 159 cm^2 x 3 cm = 477 ml x 0.15 = 72 g x 20 = 14 kcal.
Roasted vegetables 5% = 27 cm^2 x 2 cm = 53 ml x 0.6 = 32 g x 60 = 19 kcal. Oil sheen ~5 g x 880 = 44 kcal.
Total 522 g, 669 kcal.

Then, on the last line, write ANSWER: followed by JSON only:
{"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

P_DEN = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.

Then give kcal per 100 g for each item as served:
- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);
  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are
  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.
- Fat: raw leafy greens (lettuce, mixed greens, arugula, spinach, kale, chard) get "greens": true; their
  dressing is added automatically, so do not list a dressing for them. Cooked vegetables are 25-50 and get no
  oil item unless oil is visibly pooled. Other visible sauce, butter, cheese or oil: add as its own item.
- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,
  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,
  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>, "greens": <true|false>}]}"""

P_PRIOR = """This is an overhead photo of a single cafeteria serving on a plate or in a bowl.
Use the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).
Think about how much food is really there: many of these servings are small (a few pieces, a thin layer),
and the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.
Estimate the total weight of food you can see and its total food energy, including visible oil or sauce.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


RSN_CALLS = [(P_RSN, "medium", [0]), (P_RSN, "low", [0])]
DEN_CALLS = [(P_DEN, "medium", [0, 10, 20])]
PRIOR_CALLS = [(P_PRIOR, "low", [0]), (P_PRIOR, "low", [1]), (P_PRIOR, "low", [2])]


def _json(text, anchor=None):
    if anchor:
        i = text.rfind("ANSWER:")
        tail = text[i:] if i >= 0 else text
        j = tail.find(anchor)
        if j < 0:
            tail, j = text, text.rfind(anchor)
        text = tail[j:]
    return json.loads(re.search(r"\{.*\}", text, re.S).group(0))


def _items(d, oil_frac=0.0):
    items = d["items"]
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    oil = oil_frac * sum(float(i["grams"]) for i in items if i.get("greens") is True)
    return k + oil * 8.84, g + oil


def _rsn(t):
    return _items(_json(t, '{"items"'))


def _den(t):
    return _items(_json(t), OIL_FRAC)


def _prior(t):
    d = _json(t)
    return float(d["kcal"]), float(d.get("mass_g") or 0)


def _gm(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def _view(llm, image, calls, fn):
    ks, ms = [], []
    for prompt, effort, samples in calls:
        for s in samples:
            try:
                k, m = fn(llm.ask(prompt, image, model=MODEL, effort=effort, sample=s, max_tokens=8000))
            except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                continue
            if k > 0:
                ks.append(k)
                ms.append(m)
                break
    return _gm(ks), _gm(ms)


RULER = P_DEN[:P_DEN.index("\n\nThen give") + 1] + """List every distinct food, including visible sauce, dressing, oil, butter or cheese as separate items.
"""

B1 = RULER + """
Do NOT name or guess any food. For each item, describe only what is visible, precisely enough that someone who
cannot see the photo could work out what it is: color (and color variation), surface texture and grain, sheen
or oiliness, moisture or juiciness, whether it holds its shape or is soft/crumbly/flowing, piece shape and size
in cm, cut pattern, signs of cooking (browning, char, breading, frying, glaze, grill marks), and what it sits
next to or on top of.
Reply with one line per item, exactly in this form (no other text):
ITEM <number> | <visual description> | <grams>"""

HEAD = """A describer looked at a photo of a single meal and described each food item by appearance only, without naming it.
"""
B2 = HEAD + """Decide what each item is. Several foods can match one description and they can differ several-fold in energy
(lean vs fatty, dry vs watery, plain vs dressed or fried), so list the 2-4 foods that match the description,
with a probability for each (summing to 1 per item) and that food's energy in kcal per 100 g as served
(cooked weight; include cooking fat, dressing or sauce only when the description suggests it).
%s
Reply with one line per candidate food, exactly in this form (no other text):
<item number> | <food> | <probability> | <kcal per 100 g>"""

BM = HEAD + """Decide what each item is (consider the 2-4 foods that match the description, weighted by how likely each is)
and estimate its average composition per 100 g as served (cooked weight): grams of water, protein, fat and
carbohydrate. Water is the main factor: watery foods (most vegetables, fruit, broth) are 85-95 g water; cooked
grains, pasta and potato 60-75; cooked meat and fish 55-70; cheese 35-55; bread 35; fried foods 30-50; nuts,
oils, crackers and chips under 10. Water + protein + fat + carbohydrate must not exceed 100.
%s
Reply with one line per item, exactly in this form (no other text):
<item number> | <likely food> | <water> | <protein> | <fat> | <carb>"""

NUM = r"(\d+(?:\.\d+)?)"


def _b1(t):
    it = {}
    for m in re.finditer(r"ITEM\s*(\d+)\s*\|(.*?)\|\s*~?" + NUM, t):
        it[int(m.group(1))] = (m.group(2).strip(), float(m.group(3)))
    return it


def _b2(t):
    o = {}
    for m in re.finditer(r"^\s*(?:ITEM\s*)?(\d+)\s*\|([^|\n]*)\|\s*" + NUM + r"\s*\|\s*~?" + NUM, t, re.M):
        o.setdefault(int(m.group(1)), []).append((float(m.group(3)), max(float(m.group(4)), 1.0)))
    return {k: math.exp(sum(p * math.log(c) for p, c in v) / (sum(p for p, _ in v) or 1))
            for k, v in o.items() if sum(p for p, _ in v) > 0}


def _bm(t):
    o = {}
    for m in re.finditer(r"^\s*(?:ITEM\s*)?(\d+)\s*\|([^|\n]*)\|\s*" + r"\s*\|\s*".join([NUM] * 4), t, re.M):
        w, p, f, c = (float(m.group(i)) for i in range(3, 7))
        o[int(m.group(1))] = 4 * p + 4 * c + 9 * f
    return o


def _bview(llm, image):
    it = None
    for s in (0, 1):
        try:
            it = _b1(llm.ask(B1, image, model=MODEL, effort="low", sample=s, max_tokens=6000))
        except Exception:
            it = None
        if it and sum(g for _, g in it.values()) > 0:
            break
    if not it:
        return None, None
    g = {k: v[1] for k, v in it.items()}
    txt = "\n".join("ITEM %d: %s" % (k, d) for k, (d, _) in sorted(it.items()))
    ks = []
    for prompt, fn in ((B2, _b2), (BM, _bm)):
        o = fn(llm.ask(prompt % txt, None, model=MODEL, effort="low", max_tokens=6000))
        o = {k: v for k, v in o.items() if k in g and v > 0}
        if len(o) >= 0.7 * len(g):
            mean = sum(o.values()) / len(o)
            ks.append(sum(g[i] * o.get(i, mean) for i in g) / 100)
    m = sum(g.values())
    return _gm(ks), m


def views(image, llm):
    out = {}
    for name, calls, fn in (("R", RSN_CALLS, _rsn), ("DN", DEN_CALLS, _den), ("P", PRIOR_CALLS, _prior)):
        if name in USE:
            out[name] = _view(llm, image, calls, fn)
    if "B" in USE:
        out["B"] = _bview(llm, image)
    return out


def estimate(image, llm):
    v = views(image, llm)
    ok = [math.log(v[n][0] / REF) for n in USE if v[n][0]]
    if not ok:
        raise ValueError("no view parsed")
    x = sum(ok) / len(ok)  # a failed view is imputed by the others' mean
    return {"kcal": REF * math.exp(C + WM * x), "mass_g": _gm([v[n][1] for n in USE])}
