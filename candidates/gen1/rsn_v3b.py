"""rsn_v3b: same prompt as rsn_v3; aggregate on geometric mean of (low, likely, high)."""
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
STEP 7 - Uncertainty: for each item give a low and high plausible weight (the range you would be
surprised to fall outside) and your most likely weight.
STEP 8 - Sanity check: does the total weight look plausible for what is visible? Small amounts
(a few leaves, a spoon of rice) must get small weights. Estimate only what is visible; do not assume
a typical serving. Adjust if needed.

Then, on the last line, write ANSWER: followed by JSON only:
{"items": [{"name": "...", "grams_low": <number>, "grams_likely": <number>, "grams_high": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    i = text.rfind("ANSWER:")
    tail = text[i:] if i >= 0 else text
    j = tail.find('{"items"')
    if j < 0:
        j = text.rfind('{"items"')
        tail = text
    m = re.search(r"\{.*\}", tail[j:], re.S)
    return json.loads(m.group(0))


def grams_of(i):
    lo, li, hi = (max(float(i[k]), 0.1) for k in ("grams_low", "grams_likely", "grams_high"))
    return (lo * li * hi) ** (1 / 3)


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort=EFFORT, max_tokens=8000))["items"]
    g = [grams_of(i) for i in items]
    grams = sum(g)
    kcal = sum(x * float(i["kcal_per_100g"]) / 100 for x, i in zip(g, items))
    return {"kcal": kcal, "mass_g": grams}
