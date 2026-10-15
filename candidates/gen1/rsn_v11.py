"""rsn_v11: 3 chains, mean; rsn_v6 prompt, reasoning chains at several (effort, sample) settings; median of totals."""
import statistics
import json, re

MODEL = "claude-haiku-5-5"
RUNS = [("medium", 0), ("low", 0), ("low", 1)]
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.
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


def parse(text):
    i = text.rfind("ANSWER:")
    tail = text[i:] if i >= 0 else text
    j = tail.find('{"items"')
    if j < 0:
        tail = text
        j = text.rfind('{"items"')
    m = re.search(r"\{.*\}", tail[j:], re.S)
    return json.loads(m.group(0))


def one(image, llm, effort, sample):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort=effort, sample=sample, max_tokens=8000))["items"]
    grams = sum(float(i["grams"]) for i in items)
    kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return kcal, grams


def estimate(image, llm):
    res = []
    for e, s in RUNS:
        try:
            res.append(one(image, llm, e, s))
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    return {"kcal": statistics.mean(r[0] for r in res), "mass_g": statistics.mean(r[1] for r in res)}
