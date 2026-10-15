"""compB_v1 (gen2 composer B, transfer-oriented): geometric mean of three independent totals.

Components (tags from library/EXPERIENCE.md):
  - [invariant] Vessel-as-ruler geometry (plate/bowl diameter -> area -> footprint x height -> volume),
    with a generic fallback ruler (utensils, hand, can, packaging) and an angle note for non-overhead photos.
  - [invariant] Written step-by-step procedure before the answer (rsn_v6 structure): no early total,
    coverage percents must sum to the covered share, ONE bulk-density factor (void/density de-duplicated).
  - [invariant] Two reasoning chains of the same procedure at different effort (medium, low) = resampling.
  - [domain]    Separate identification/energy-density view: look-alike foods differ several-fold in
    kcal/100 g (phrased generically, multi-cuisine examples), cooked-weight reference values (generic food
    knowledge), fat counted only when visible and sized to what is seen (no percentage rule).
  - [invariant] Averaging low-correlation views: the density view's log-error correlation with the geometry
    procedure is ~0.65 vs ~0.85 for resampling the same prompt; combined by geometric mean (no weights).
  - [invariant] Per-view retry on parse failure with a different sample index; geomean of available views.
No fitted constants: no global scale, no calibration map, no fixed frame width, no dataset kcal priors,
no rules derived from Nutrition5k label statistics. All numbers in prompts are generic food/tableware facts.
"""
import json, math, re

MODEL = "claude-haiku-5-5"

RSN = """This is a photo of a meal. Estimate the weight and food energy of the food you can see.
Work through these steps in writing, briefly, before giving the answer.

STEP 1 - Scene: what kind of meal is this, and from what angle is it photographed? (Do not guess a total yet.)
STEP 2 - Ruler: identify the plate/bowl/container and its likely diameter or width in cm (dinner plate ~26 cm,
side plate ~20 cm, cereal bowl ~15 cm, small dish ~8 cm). If the photo is taken at an angle, size the vessel
from its longest (undistorted) width. If there is no vessel, use a fork (~19 cm), spoon, hand, can or
packaging as the ruler. Vessel area = 3.14 x (diameter/2)^2. Food on other plates at the edge of the photo
is not part of this meal.
STEP 3 - Items: list every distinct visible food, including oil, dressing or sauce when you can see them.
STEP 4 - Area: for each item, the percent of the vessel area it covers. These percents must add up to the
share of the vessel actually covered by food (check this; if food covers most of the plate they should
add up to most of 100%).
STEP 5 - Volume: area (cm^2) x typical height (cm) = gross volume in ml, measured as the outer envelope
of the pile. Do not reduce it here. For countable pieces, size each piece from its visible dimensions
against the ruler, not from what a typical piece weighs.
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

DENS = """This is a photo of a meal. Estimate each food's weight and its energy density.
Use the plate, bowl or container as a ruler (dinner plate ~26 cm, side plate ~20 cm, bowl ~15 cm; with no
vessel use cutlery, a hand or packaging). For each food item judge its footprint and height, then its weight
in grams from that volume. Estimate only what is visible; do not assume a typical serving. Small amounts
(a few leaves, a spoon of rice) must get small weights.

Then give kcal per 100 g for each item as served. Identification matters as much as size:
- Look-alike foods differ several-fold in energy. Before naming an item, consider what else it could be and
  decide from texture, sheen, shape and the rest of the meal: egg white vs cheese crumbles, cauliflower vs
  rice, squash vs cheese cubes, olives vs dates, tofu vs paneer, white sauce vs yogurt, beans vs meat crumbles.
- Use cooked, as-served values: grains, pasta and noodles are cooked weights.
- Fat: count oil, butter, dressing, cheese or creamy sauce only when you can see it (gloss, pooling, coating,
  melted layer), as its own item sized to what you see. Do not assume hidden fat. Plain cooked vegetables 25-50.
- Reference values (kcal/100 g): leafy greens 15-20, vegetables 25-40, fruit 50-70, cooked rice 130,
  cooked pasta or noodles 140-160, potato boiled 85 / roasted 130 / fries 300, bread 260, tortilla 300,
  naan 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500, fish 140-200, shrimp 100,
  egg 150, egg white 55, tofu 80-120, beans or lentils 120-140, curry or stew 100-180, dumplings 200-250,
  cheese 350-400, yogurt 60-100, hummus 170, avocado 160, nuts 600, oil 880, butter 720,
  creamy dressing 400-500, cake or pastry 350-450.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

VIEWS = [(RSN, "medium", 8000), (RSN, "low", 8000), (DENS, "medium", 4000)]


def parse(text):
    i = text.rfind("ANSWER:")
    tail = text[i:] if i >= 0 else text
    j = tail.find('{"items"')
    if j < 0:
        tail, j = text, text.rfind('{"items"')
    m = re.search(r"\{.*\}", tail[max(j, 0):], re.S)
    return json.loads(m.group(0))


def totals(items):
    g = k = 0.0
    for it in items:
        gi = float(it["grams"])
        ki = float(it["kcal_per_100g"])
        if gi < 0 or ki < 0 or gi != gi or ki != ki:
            raise ValueError("bad item")
        g += gi
        k += gi * ki / 100
    if g <= 0 or k <= 0:
        raise ValueError("empty")
    return k, g


def view(image, llm, prompt, effort, max_tokens):
    for s in (0, 1, 2):
        try:
            return totals(parse(llm.ask(prompt, image, model=MODEL, effort=effort, sample=s,
                                        max_tokens=max_tokens))["items"])
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return None


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def estimate(image, llm):
    ests = [e for e in (view(image, llm, p, eff, mt) for p, eff, mt in VIEWS) if e]
    if not ests:
        raise ValueError("no parsable view")
    return {"kcal": gmean([e[0] for e in ests]), "mass_g": gmean([e[1] for e in ests])}
