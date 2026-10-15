"""gen3 G_v1: vessel-and-depth written reasoning (between-dish scale view).

Components (tag):
  [invariant] vessel classified by visual cues (shape, rim width vs diameter, visible inner wall, food below rim,
              inner shadow) into flat plate / shallow bowl / deep bowl / box / cup, and its size reconciled from
              two cues: type prior and a known-size object counted across the vessel.
  [invariant] depth measured by counting: thickness = piece size x number of pieces stacked at the thickest point
              (the model's written cm heights are ~constant, r=0.03 with mass, gen2), mound vs layer averaging.
  [invariant] bowls: food volume = fill fraction x bowl capacity (capacity from width and depth), not footprint x height.
  [invariant] explicit hidden-food question: base layers under toppings, pieces below the visible surface.
  [domain]    standard countable pieces weighed by count x one piece weight (scale-free).
  [domain]    generic vessel sizes (dinner plate 25-28 cm, side plate 18-22, small paper plate 15-18, cereal bowl
              14-16, serving bowl 20-25, ramekin 7-10).
No fitted constants.
"""
import json, re, math

MODEL = "claude-haiku-5-5"

PROMPT = """Overhead photo of food in a vessel. Estimate the weight and energy of the food. The two hardest parts
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
STEP 4 - Hidden food: is there a base layer (rice, grains, greens, sauce) under the toppings, or food below the
visible surface? Add it as items. Large heaped plates and full bowls often weigh 500-900 g; a few pieces on a
large plate stay a few grams.
STEP 5 - kcal per 100 g for each item as served (cooked weight).
Then on the last line write ANSWER: followed by JSON only:
{"vessel": "...", "width_cm": <n>, "items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    return d if v != v else min(max(v, lo), hi)


def parse(text):
    i = text.rfind("ANSWER")
    tail = text[i:] if i >= 0 else text
    m = re.search(r"\{.*\}", tail, re.S) or re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def total(d):
    g = k = 0.0
    for it in d["items"]:
        gi = num(it.get("grams"), 0, 3000, 0)
        g += gi
        k += gi * num(it.get("kcal_per_100g"), 0, 900, 150) / 100
    return k, g


def estimate(image, llm):
    for s in (0, 1, 2):
        try:
            k, g = total(parse(llm.ask(PROMPT, image, model=MODEL, effort="low", sample=s, max_tokens=8000)))
            if k > 0 and g > 0:
                return {"kcal": k, "mass_g": g}
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    raise ValueError("no parsable estimate")
