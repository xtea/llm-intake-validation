"""gen2 discrimination v4: count x measured dimensions. For each item the model counts the pieces (a pile counts as
one piece) and measures ONE typical piece (or the whole pile) in cm: length x width x height, using the vessel and
objects of known size as rulers, plus its shape. Volume = L x W x H x shape factor (box 1, rounded / mound /
wedge ~0.5, which are geometric constants), grams = volume x density, all in code. v3 (household units) raised
mass slope to 0.97 on dev but its coarse units over-sized flat pieces; dimensions are the literal version."""
import json, re

MODEL = "claude-haiku-5-5"
SHAPE = {"box": 1.0, "cylinder": 0.785, "round": 0.524, "mound": 0.5, "wedge": 0.5, "irregular": 0.6}
PROMPT = """Overhead photo of food on a plate, bowl or container. Measure the food; do not guess weights.

First find the scale: a dinner plate is ~26 cm across, a side plate ~20 cm, a cereal bowl ~15 cm, a large salad
or mixing bowl ~28 cm. Cross-check with things of known size (fork ~19 cm, cherry tomato ~2.5 cm, egg ~5.5 cm,
bread slice ~11 cm) and state how many cm one tenth of the vessel's width is.

For each distinct food item (include visible oil, dressing or sauce):
- "count": the number of separate pieces. COUNT discrete pieces (cubes, slices, florets, berries, nuggets,
  wedges, links), counting in rows or groups and including pieces partly hidden under others. A continuous pile
  or spread (rice, mash, stew, a bed of greens, sauce) is count 1.
- "l_cm", "w_cm", "h_cm": length, width and height (thickness) of ONE typical piece, or of the whole pile if
  count is 1. Measure against the vessel; height from shadows, stacking and how far the food rises (a sauce smear
  0.2, a meat slice 1, a single layer of chunks 2, pieces stacked on pieces 3-4, a heaped mound 5+; food inside a
  bowl reaches down to the bowl's floor).
- "shape": box (slices, cubes, bars), cylinder (links, carrot sticks, a flat disc), round (balls, berries,
  tomatoes, eggs), mound (a heap or pile, a domed portion), wedge (pizza or pie slices, triangles),
  irregular (florets, chicken pieces, leaves).
- "density": g per cm3 of that envelope: leafy greens 0.15, florets / chopped raw vegetables 0.5, cooked
  vegetables / fruit 0.7, rice / grains / pasta 0.8, meat, fish, egg, cheese, potato, sauce 1.0, bread 0.35.
- "kcal_per_100g": energy density as served.
Measure what you see; do not assume a typical serving.
Reply with JSON only:
{"cm_per_tenth": <number>, "items": [{"name": "...", "count": <number>, "l_cm": <number>, "w_cm": <number>,
  "h_cm": <number>, "shape": "box|cylinder|round|mound|wedge|irregular", "density": <number>,
  "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def num(x, lo, hi, d):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return d
    return d if v != v else min(max(v, lo), hi)


def item_g(it):
    vol = (num(it.get("l_cm"), 0.1, 40, 3) * num(it.get("w_cm"), 0.1, 40, 3) * num(it.get("h_cm"), 0.05, 15, 1)
           * SHAPE.get(str(it.get("shape", "")).lower().strip(), 0.6))
    return num(it.get("count"), 1, 300, 1) * vol * num(it.get("density"), 0.05, 1.3, 0.8)


def total(obs):
    g_tot = k_tot = 0.0
    for it in obs["items"]:
        g = item_g(it)
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
