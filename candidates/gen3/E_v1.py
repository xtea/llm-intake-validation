"""E_v1 (gen3 mutator E): compA with its most-correlated views swapped for the least-correlated ones.
kcal = REF*exp(C + WM*mean_i ln(v_i/REF)), equal view weights, 2 fitted constants. 4 Haiku calls (~2.7 m$/dish).
Components (tag):
  view R  [invariant] rsn_v6 written procedure (vessel -> item area % -> volume -> ONE bulk density -> kcal),
          2 chains (medium s0, low s0), geometric mean. Byte-identical to compA_v4 P_RSN.
  view U  [invariant]+[domain] disc_v6 household-unit counting (tsp/tbsp/ping-pong/deck/tennis ball/cup, or
          pieces x one piece), grams = units x ml x density in code; medium (retry s1). Byte-identical to disc_v6.
  view A  [domain] compC_v5 den_v3 item list: look-alike identification rules, as-served kcal/100 g refs, VISUAL
          dressing rule (glossy leaves +5% at 700 kcal/100 g); low (retry s1). Byte-identical to compC_v5 P_DEN.
  Dropped vs compA_v4: DN (den_v4, [dataset] OIL_FRAC rule; r=0.83 with A) and P (cafeteria prior, 3 calls;
  r=0.90 with the compA composite). U is the least correlated with the compA composite (0.67; G 0.71, A 0.85,
  DN 0.87, P 0.90) and with DN/A (0.49/0.57). U reads ~20% heavy; C absorbs it.
  calibration [dataset] C, WM fitted (coordinate search, min sum|est-true| = mae_pct_of_mean) on the 597 rows of
  search --n 600 --seed g3 ONLY with all views parsed. A failed view is imputed by the mean of the others.
  Fitted: C=-0.1441, WM=0.8831. g3 in-sample 29.75, 5-fold x4 cv 29.96 (compA_v4 views refit on the same rows: cv 31.32).
  g3b-unseen (380): 32.27 vs compA views refit on g3 31.54 -> U's g3 gain did NOT transfer; mass slope .87 vs .77.
"""
import json, re, math

MODEL = "claude-haiku-5-5"
REF = 300.0
C = -0.1441
WM = 0.8831
UNIT_ML = {"tsp": 5.0, "tbsp": 15.0, "pingpong": 30.0, "deck": 60.0, "tennisball": 120.0, "cup": 240.0}

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

P_UNITS = """Overhead photo of food on a plate, bowl or container. Measure each food in household volume units
by comparing it with mental reference objects, like a dietitian doing a portion-size interview.

Reference units (standard portion-size aids; volume of the food including the air between pieces):
  tsp         5 ml  a teaspoon / the tip of a thumb / one die: a dab of sauce, one olive, a few seeds
  tbsp       15 ml  a tablespoon / a whole thumb: a small spoonful, one 2.5 cm cube
  pingpong   30 ml  a ping-pong ball (2 tbsp): an egg-yolk-sized lump, a meatball, a small scoop
  deck       60 ml  a deck of cards (9 x 6 x 1.5 cm): for FLAT things - a fillet, a slice of pizza or meat
  tennisball 120 ml a tennis ball / half a cup: a scoop of rice, a fist-sized potato
  cup       240 ml  a baseball / one cup: a large scoop, a mound the size of a fist and a half
Flat pieces are measured by area x thickness, so compare them with the deck of cards, not with balls
(a thin 12 x 10 cm slice 1 cm thick is about 1 deck).

Use the vessel as a ruler: a dinner plate (~26 cm) can hold about 4 cups of food spread 2 cm deep over its
whole area; a cereal bowl (~15 cm) filled to the rim holds about 2 cups; a large salad bowl holds 6-8 cups.
For each distinct food item (include visible oil, dressing or sauce):
- if it is discrete pieces you can count (cubes, slices, florets, berries, nuts, nuggets, wedges), COUNT them
  (count rows or groups; include pieces partly hidden under others) and give the size of ONE piece in units,
  using fractions for small pieces: one almond 0.2 tsp, one grape or olive 1 tsp, one cherry tomato 3 tsp,
  one 2 cm meat cube 0.5 tbsp, one broccoli floret 1 tbsp, one chicken drumstick 1 tennisball;
- otherwise give how many units the whole pile is (e.g. 3 tbsp, 1.5 tennisball, 2 cup). Pick the unit that
  needs a count between 1 and 6. A cup is a lot: a mound as big as a fist and a half.
Count what you see; do not assume a typical serving. Also give the density in g/ml: for a pile its bulk density
including air (leafy greens 0.15, chopped vegetables 0.5, rice / grains / scrambled egg 0.8, mash, meat, fish,
cheese, sauce 1.0); for one counted piece the density of the piece itself (vegetables, fruit, nuts 0.8,
bread or waffle 0.35, meat, fish, egg, cheese 1.0). White cubed or crumbled food can be egg white, tofu, potato or
cheese: check texture and context before choosing, cheese has about four times the energy.
Give kcal per 100 g as served.
Reply with JSON only:
{"items": [{"name": "...", "pieces": <count or 0 if not discrete>, "unit": "tsp|tbsp|pingpong|deck|tennisball|cup",
            "units": <number of units: per piece if pieces > 0, else for the whole pile>,
            "density": <number>, "kcal_per_100g": <number>}]}"""

P_DEN = "This is an overhead photo of a meal on a plate or in a bowl.\nUse the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,\na cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)\nand its height, then estimate its weight in grams from that volume. Estimate only what is visible;\ndo not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.\n\nThen give kcal per 100 g for each item as served:\n- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);\n  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are\n  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.\n- Fat: judge from the photo. Leaves or vegetables that look glossy, wet or coated are dressed: add a separate\n  \"dressing/oil\" item of about 5% of their weight at 700 kcal/100 g. Dry, matte leaves get no dressing.\n  Cooked vegetables are 25-50 unless visibly oily. Visible sauce, butter, cheese or oil: add as its own item.\n- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,\n  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,\n  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.\nReply with JSON only: {\"items\": [{\"name\": \"...\", \"grams\": <number>, \"kcal_per_100g\": <number>}]}"

RSN_CALLS = [(P_RSN, "medium", [0]), (P_RSN, "low", [0])]


def _obj(text, anchor=None):
    if anchor:
        i = text.rfind("ANSWER:")
        tail = text[i:] if i >= 0 else text
        j = tail.find(anchor)
        if j < 0:
            tail, j = text, text.rfind(anchor)
        text = tail[j:]
    return json.loads(re.search(r"\{.*\}", text, re.S).group(0))


def _num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    return d if v != v else min(max(v, lo), hi)


def _items(items):
    g = sum(float(i["grams"]) for i in items)
    k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return k, g


def _rsn(t):
    return _items(_obj(t, '{"items"')["items"])


def _den(t):
    return _items(_obj(t)["items"])


def _units(t):
    g_tot = k_tot = 0.0
    for it in _obj(t)["items"]:
        ml = UNIT_ML.get(str(it.get("unit", "")).lower().replace(" ", "").replace("_", ""), 15.0)
        n = _num(it.get("units"), 0, 50, 1)
        p = _num(it.get("pieces"), 0, 300, 0)
        g = ml * n * (p if p >= 1 else 1) * _num(it.get("density"), 0.05, 1.3, 0.8)
        g_tot += g
        k_tot += g * _num(it.get("kcal_per_100g"), 0, 900, 150) / 100
    return k_tot, g_tot


def _gm(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def _view(llm, image, calls, fn):
    """calls: [(prompt, effort, [sample, retry samples...])]; one parsed answer per entry, geometric mean."""
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


VIEWS = ((RSN_CALLS, _rsn), ([(P_UNITS, "medium", [0, 1])], _units), ([(P_DEN, "low", [0, 1])], _den))


def estimate(image, llm):
    views = [_view(llm, image, c, fn) for c, fn in VIEWS]
    ok = [math.log(k / REF) for k, _ in views if k]
    if not ok:
        raise ValueError("no view parsed")
    mean = sum(ok) / len(ok)
    x = [math.log(k / REF) if k else mean for k, _ in views]  # a failed view is imputed by the others' mean
    z = C + WM * sum(x) / len(x)
    return {"kcal": REF * math.exp(z), "mass_g": _gm([m for _, m in views])}
