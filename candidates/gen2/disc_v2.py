"""gen2 discrimination v2: cal_v3's literal-geometry JSON prompt (highest Haiku mass slope in gen1, 0.91) plus a
forced per-item height class (gen1 heights were constant and uncorrelated with mass), overlapping layers allowed,
and a known-size cross-check for the container. No calibration."""
import json, re, math

MODEL = "claude-haiku-5-5"
PROMPT = """Overhead photo of food on a plate, bowl or container. Estimate each item's weight by geometry, not by
what a typical serving would be.

1. Identify the container and its inner diameter in cm (dinner plate ~26, side plate ~20, bowl ~15, large salad or
   mixing bowl ~28, small cup ~9). Check it against things of known size in the photo (fork ~19 cm, cherry tomato
   ~2.5 cm, egg ~5.5 cm, bread slice ~11 cm, a meat cube ~2 cm). Its area is pi*(d/2)^2 cm2.
2. For each food item: the fraction of the container area its layer covers (layers may overlap: food lying on top of
   other food keeps its own area, so fractions can add up to more than 1), and its height class from what you see:
   film 0.3 cm (sauce smear, scattered seeds) | flat 1 cm (one thin layer, plate visible under or between pieces) |
   layer 2 cm (one layer of chunks, a low bed of rice or greens) | stacked 3.5 cm (pieces resting on other pieces,
   plate hidden) | heap 5-6 cm (a mound higher in the middle than at its edges, casting shadows) | bowl (food inside a
   bowl: depth = filled fraction of the bowl's depth, bowl depth ~1/3 of its diameter).
   Then volume = area * height and grams = volume * bulk density (leafy greens ~0.1-0.2, chopped vegetables ~0.5,
   rice/pasta/meat ~0.8-1.0, sauces ~1.0 g/cm3).
   Give grams_low and grams_high bracketing the real weight, then your best grams. A few pieces stay a few grams:
   do not round small items up to a serving, and do not shrink a heaped plate or full bowl down to one either.
3. kcal_per_100g for the item as served (cooked weight): e.g. cooked rice ~130, cooked chicken breast ~165,
   roasted potatoes ~150, steamed vegetables ~30-40, raw salad greens ~15-20, fruit ~50, scrambled eggs ~150,
   bacon ~500, cheese ~400. Count visible oil, butter or dressing as its own item.
Reply with JSON only:
{"container_cm": <number>, "items": [{"name": "...", "area_frac": <number>, "height": "film|flat|layer|stacked|heap|bowl", "grams_low": <number>, "grams_high": <number>, "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def total(items):
    g_tot = k_tot = 0.0
    for i in items:
        g = float(i.get("grams") or 0)
        lo, hi = float(i.get("grams_low") or g), float(i.get("grams_high") or g)
        if lo > 0 and hi > 0 and g > 0:
            g = math.exp((math.log(lo) + math.log(hi) + math.log(g)) / 3)
        g_tot += g
        k_tot += g * float(i["kcal_per_100g"]) / 100
    return k_tot, g_tot


def estimate(image, llm):
    for s in (0, 1):
        try:
            k, g = total(parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s))["items"])
            if k > 0 and g > 0:
                return {"kcal": k, "mass_g": g}
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    raise ValueError("no parsable estimate")
