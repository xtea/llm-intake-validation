"""rsn_v4: rsn_v2 procedure + two generic worked examples at very different scales."""
import json, re

MODEL = "claude-haiku-5-5"
EFFORT = "medium"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.
Work through these steps in writing, briefly, before giving the answer.

STEP 1 - Scene: what kind of meal is this, and roughly how much food is there overall?
STEP 2 - Vessel: identify the plate/bowl/container and its likely diameter in cm (dinner plate ~26 cm,
side plate ~20 cm, cereal bowl ~15 cm, small sauce dish ~8 cm). Note how much of the frame it fills.
STEP 3 - Items: list every distinct visible food, including oil, dressing or sauce when you can see them.
STEP 4 - Volume: for each item, state the fraction of the vessel area it covers, convert that to an
area in cm^2 (vessel area = 3.14 x (diameter/2)^2), and estimate its average height in cm.
Volume (ml) = area x height. Account for gaps, leafy/airy foods (much less dense than solid volume)
and pieces that are thin or scattered.
STEP 5 - Grams: convert volume to grams with a sensible bulk density (leafy greens ~0.1-0.3 g/ml,
cut vegetables/fruit ~0.5-0.7, rice/pasta/grains ~0.7-0.9, meat/fish/egg ~1.0, sauces ~1.0).
STEP 6 - Energy: give kcal per 100 g for each item as plated (cooked weight), and multiply.
STEP 7 - Sanity check: does the total weight look plausible for what is visible? Small amounts
(a few leaves, a spoon of rice) must get small weights. Estimate only what is visible; do not assume
a typical serving. Adjust if needed.

Two worked examples (generic, for the arithmetic and the range of scales only):

Example A (small): side plate 20 cm (area ~314 cm^2). A few cherry tomatoes covering 5% (16 cm^2) x 2.5 cm
high = 40 ml x 0.6 = 24 g at 18 kcal/100g = 4 kcal. A slice of cheese covering 8% (25 cm^2) x 0.3 cm
= 8 ml x 1.1 = 8 g at 400 kcal/100g = 32 kcal. Total ~32 g, ~36 kcal. Most of the plate is empty.

Example B (large): dinner plate 26 cm (area ~530 cm^2). Cooked rice covering 30% (160 cm^2) x 2 cm high
= 320 ml x 0.8 = 255 g at 130 kcal/100g = 330 kcal. Grilled chicken pieces covering 20% (106 cm^2)
x 1.5 cm = 160 ml x 0.9 (gaps) = 145 g at 165 kcal/100g = 240 kcal. Mixed leaves covering 25%
(133 cm^2) x 3 cm = 400 ml x 0.15 = 60 g at 20 kcal/100g = 12 kcal. Oil sheen ~5 g at 880 kcal/100g = 44 kcal.
Total ~465 g, ~626 kcal.

Then, on the last line, write ANSWER: followed by JSON only:
{"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    i = text.rfind("ANSWER:")
    tail = text[i:] if i >= 0 else text
    j = tail.find('{"items"')
    if j < 0:
        j = text.rfind('{"items"')
        tail = text
    m = re.search(r"\{.*\}", tail[j:], re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort=EFFORT, max_tokens=8000))["items"]
    grams = sum(float(i["grams"]) for i in items)
    kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return {"kcal": kcal, "mass_g": grams}
