"""gen2 discrimination v6: household-measure counting (the portion-size aid used in dietary recall).
For each item the model counts reference units of volume (tsp 5, tbsp 15, ping-pong ball 30, deck of cards 60 for
flat pieces, tennis ball / half cup 120, baseball / cup 240 ml), or for discrete pieces counts them and sizes ONE
piece in the same units (fractions for small pieces). Grams = units x unit volume x density, in code.
Why: gen1 written heights were constant (r=0.03 with true mass) and footprints saturate on full plates; counting
units scales linearly with portion instead of being pulled toward a typical serving.
v3 (first unit version) -> v5 (deck-of-cards for flat pieces, dietetic anchors) -> v6 (fractional per-piece
sizes, piece vs pile density, white-food identity check)."""
import json, re

MODEL = "claude-haiku-5-5"
UNIT_ML = {"tsp": 5.0, "tbsp": 15.0, "pingpong": 30.0, "deck": 60.0, "tennisball": 120.0, "cup": 240.0}
PROMPT = """Overhead photo of food on a plate, bowl or container. Measure each food in household volume units
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


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    return d if v != v else min(max(v, lo), hi)


def total(obs):
    g_tot = k_tot = 0.0
    for it in obs["items"]:
        ml = UNIT_ML.get(str(it.get("unit", "")).lower().replace(" ", "").replace("_", ""), 15.0)
        n = num(it.get("units"), 0, 50, 1)
        p = num(it.get("pieces"), 0, 300, 0)
        g = ml * n * (p if p >= 1 else 1) * num(it.get("density"), 0.05, 1.3, 0.8)
        g_tot += g
        k_tot += g * num(it.get("kcal_per_100g"), 0, 900, 150) / 100
    return k_tot, g_tot


def estimate(image, llm):
    for s in (0, 1):
        try:
            k, g = total(parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s)))
            if k > 0 and g > 0:
                return {"kcal": k, "mass_g": g}
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    raise ValueError("no parsable estimate")
