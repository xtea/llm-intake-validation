"""gen2 discrimination v1: written plate-as-ruler procedure (rsn_v6 skeleton) with the HEIGHT step rewritten.
Diagnosis (gen1 cached outputs): item heights written by Haiku are ~constant (1.5/2 cm, copied from the worked
example) and have zero correlation with true mass (r=0.03); footprint saturates on full plates, so heavy plates are
under-read. Here height is a forced visual decision per item (flat / one layer / stacked / heap / bowl fill), layers
are allowed to overlap (an item under another keeps its own area), the vessel size is cross-checked against
objects of known size, and the worked examples span the extremes of height."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl. Estimate its weight and energy.
Work through these steps in writing, briefly, before giving the answer.

STEP 1 - Scene: what kind of meal is this? (Do not guess a total weight yet.)
STEP 2 - Vessel: identify the plate/bowl and its diameter in cm. Typical: side plate ~20, dinner plate ~26,
cereal bowl ~15, large salad or mixing bowl 25-32. Cross-check it against things of known size in the photo
(a fork ~19 cm long, a cherry tomato ~2.5 cm, an egg ~5.5 cm, a broccoli floret head ~4 cm, a bread slice
~11 cm, a diced cube of meat ~2 cm): how many of them would fit across the vessel? Area = 3.14 x (d/2)^2.
Food on other plates at the edge of the photo is not part of this meal.
STEP 3 - Items: list every distinct visible food, including oil, dressing or sauce when you can see them.
STEP 4 - Area: for each item, the percent of the vessel area its layer occupies. Layers may overlap: if one
food lies on top of another (chicken on a bed of greens, sauce over rice), each keeps its own area, so the
percents may add up to more than 100.
STEP 5 - Height: this is the step that decides the weight of a full plate, so decide it per item from what
you see, choosing one class and saying which cue you used:
  film   ~0.3 cm  sauce smear, scattered seeds, a drizzle
  flat   ~1 cm    a single thin layer, you can see the plate between or under the pieces (sliced meat, a spread)
  layer  ~2 cm    one layer of chunks or a low bed of rice / greens
  stacked ~3.5 cm pieces resting on other pieces, two or more layers, plate hidden underneath
  heap   ~5-6 cm  a mound clearly higher in the middle than at its edges, casting shadows, piled above the rim
  bowl   for food inside a bowl: food depth = (fraction of the bowl's depth that is filled) x bowl depth,
         where bowl depth is ~1/3 of its diameter (deep mixing bowls ~1/2). Little bowl wall visible above the
         food means the bowl is nearly full.
  Cues: shadows at the base of piles, pieces lying on other pieces, how much plate or bowl floor shows
  between pieces, how much of the bowl wall is visible above the food. Do not give every item the same height.
STEP 6 - Volume and grams: area (cm^2) x height (cm) = gross volume in ml; grams = volume x bulk density.
The bulk density already accounts for air and gaps; apply no other reduction. Typical bulk densities (g/ml):
loose leafy greens 0.1-0.2 (wilted or dressed greens 0.3), cut vegetables / fruit pieces 0.5-0.7,
rice / pasta / grains 0.8, mashed or dense items, meat, fish, egg, cheese 0.9-1.0 (bread loaf ~0.3), sauces 1.0.
STEP 7 - Energy: kcal per 100 g for each item as plated (cooked weight); multiply.
STEP 8 - Check: do NOT pull the total toward a typical serving. A sparse plate must stay light and a heaped
plate or a full deep bowl must stay heavy (a full deep bowl or heaped dinner plate can hold 500-900 g).

Two worked examples (generic, only to show the arithmetic and the range of scales):

Example A (light): side plate 20 cm, area 314 cm^2. Cherry tomatoes 6% = 19 cm^2, layer 2.5 cm (single
tomatoes, plate visible around them) = 47 ml x 0.6 = 28 g x 18 kcal/100g = 5 kcal. Cheese slice 9% = 28 cm^2,
flat 0.3 cm = 8 ml x 1.0 = 8 g x 400 = 32 kcal. Total 36 g, 37 kcal.

Example B (heavy): large bowl 28 cm (about 14 meat cubes across), area 615 cm^2, little wall visible, so the
food fills ~2/3 of a ~9 cm depth = 6 cm. Greens and broccoli bed 80% = 492 cm^2 x 5 cm (bowl fill minus the
top layer) = 2460 ml x 0.25 = 615 g x 30 = 185 kcal. Diced chicken on top 45% = 277 cm^2, stacked 2 cm extra
layer = 554 ml x 0.6 = 332 g x 165 = 548 kcal. Dressing ~20 g x 450 = 90 kcal. Total 967 g, 823 kcal.

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


def estimate(image, llm):
    for s in (0, 1):
        try:
            items = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s, max_tokens=8000))["items"]
            g = sum(float(i["grams"]) for i in items)
            k = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
            if g > 0 and k > 0:
                return {"kcal": k, "mass_g": g}
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    raise ValueError("no parsable estimate")
