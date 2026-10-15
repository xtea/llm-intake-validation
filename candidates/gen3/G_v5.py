"""gen3 G_v5: compA_v4 views R, DN, P (prompts byte-identical) + 4th view G = G_v4, equal weights, 2-constant power law.
Tags: R [invariant] written reasoning; DN [domain]+[dataset] density rules (OIL_FRAC [dataset]); P [dataset] cafeteria
prior; G [invariant] vessel type by cues, size from type + known-size object, depth by counting stacked pieces, bowls
by fill x capacity, hidden-food step, [domain] typical thicknesses + 2 generic worked examples (gen3/G_v4.py).
Calibration [dataset]: kcal = REF*exp(C + (WM/4)*sum ln(v_i/REF)); C=-0.1125, WM=0.9525 fitted (grid + pattern search,
min sum|est-true|) on search --n 600 --seed g3 only. fe.evaluate: g3 30.70 (compA_v4 31.85);
g3b minus g3 (380): 30.71 vs compA_v4 31.39, diff 90% CI [-1.42, 0.05]. Cost ~3.9 m$/dish uncached (7 Haiku calls).
"""
import json, re, math

MODEL = "claude-haiku-5-5"
REF = 300.0
OIL_FRAC = 0.09
C = -0.1125
WM = 0.9525
W = [WM / 4] * 4                       # weights for (R, DN, P, G)

P_G = """Overhead photo of food in a vessel. Estimate the weight and energy of the food. The two hardest parts
are the SIZE of the vessel and the DEPTH of the food, so work them out explicitly. Write briefly, step by step.

STEP 1 - Vessel type. Choose: flat plate (round / square / paper) / shallow bowl / deep bowl / takeout box /
cup or ramekin. Cues: a flat plate shows a rim band and a flat centre with no inner wall; a bowl shows a curved
inner wall, more of it on one side, and a shadow inside; in a deep bowl the food surface sits well below the rim.
STEP 2 - Vessel size, from two cues, then reconcile:
 a) type: round dinner plate 25-28 cm, side or salad plate 18-22, small paper plate 15-18, large paper plate 22-26,
    square plates 20-30, cereal bowl 14-16 (holds ~500 ml), serving or salad bowl 20-25 (~1.5-2.5 l), ramekin 7-10.
    Do not default to 26 cm: decide whether THIS vessel is small, medium or large.
 b) a reference object of known size in the photo (a fork 19 cm, a spoon, an almond 2.3 cm, an olive or grape 2.2 cm,
    a cherry tomato 3 cm, a broccoli floret 4 cm, an egg 5.5 cm, a bread slice 11 cm, a chicken drumstick 11 cm):
    how many of its lengths fit across the vessel? width = count x length.
 Final width = the cue you trust more, or between them.
STEP 3 - Each food item (include visible sauce, dressing, oil):
 - countable standard pieces (nuts, olives, berries, grapes, cherry tomatoes, eggs, nuggets, meatballs, shrimp,
   slices of bread or pizza, drumsticks): count the visible ones, then add the ones hidden underneath (a pile
   2 pieces deep hides roughly as many as you see); grams = count x one piece (almond 1.2 g, olive 4, grape 5,
   cherry tomato 15, egg 50, bread slice 30, nugget 18, meatball 30, drumstick 90).
 - on a plate: footprint = percent of the vessel area x vessel area (round: 0.785 x width^2; square: width^2).
   Thickness by counting, not by guessing cm: size of one piece or grain clump x how many are stacked at the
   thickest point; a mound averages about half its peak, a flat layer is its full thickness. Grams = footprint x
   average thickness x bulk density.
 - in a bowl: capacity = 0.35 x width^3 / 1000 litres for a deep bowl, 0.2 x width^3 / 1000 for a shallow bowl;
   fill = fraction of the depth filled (1.0 = level with the rim; a heap above the rim is more); food volume =
   capacity x fill x fill; grams = volume x bulk density, split among the items by their share.
 - bulk densities (g/ml): raw leafy greens 0.15, cooked leafy greens 0.6, chopped vegetables or fruit 0.6,
   rice, grains, pasta, scrambled egg 0.8, meat, fish, egg, cheese, mash, sauce 1.0, bread 0.3.
 - typical thickness (check your count against these): a fish fillet or chicken breast 2-3 cm, a steak or
   chop 2 cm, a slice of bread or pizza 1.5 cm, a mound of rice or grains 3-5 cm at the centre, a pile of chunky
   pieces (egg, potato, fruit cubes) 4-6 cm at the centre, a smear of sauce 0.3 cm, loose leaves 3-6 cm.
STEP 4 - Hidden food: is there a base layer (rice, grains, greens, sauce) under the toppings, or food below the
visible surface? Add it as items. Large heaped plates and full bowls often weigh 500-900 g; a few pieces on a
large plate stay a few grams.
STEP 5 - kcal per 100 g for each item as served (cooked weight).
Two generic examples of the arithmetic: (A) small: side plate 20 cm, 8 olives x 4 g = 32 g, plus a strip of
cheese 3 x 6 cm x 0.5 cm = 9 ml x 1.0 = 9 g; total 41 g. (B) large: square plate 27 cm (729 cm2): rice 25% = 182 cm2 x
2 cm average (4 cm peak) = 364 ml x 0.8 = 291 g; salmon fillet 12 x 8 cm x 0.8 = 77 cm2 x 2.5 cm = 192 g; broccoli 15%
= 109 cm2 x 2.5 cm = 273 ml x 0.5 = 137 g; total 620 g.
Then on the last line write ANSWER: followed by JSON only:
{"vessel": "...", "width_cm": <n>, "items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

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
G_CALLS = [(P_G, "low", [0, 1, 2])]
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


def _g(t):
    d = _json(t, '{"vessel"')
    return _items(d)


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


def estimate(image, llm):
    views = [_view(llm, image, c, fn) for c, fn in
             ((RSN_CALLS, _rsn), (DEN_CALLS, _den), (PRIOR_CALLS, _prior), (G_CALLS, _g))]
    ok = [math.log(k / REF) for k, _ in views if k]
    if not ok:
        raise ValueError("no view parsed")
    mean = sum(ok) / len(ok)
    x = [math.log(k / REF) if k else mean for k, _ in views]  # a failed view is imputed by the others' mean
    z = C + sum(w * xi for w, xi in zip(W, x))
    return {"kcal": REF * math.exp(z), "mass_g": _gm([m for _, m in views])}
