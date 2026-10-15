"""cal_v3: geometric de-biasing prompt (container size -> per-item area cm2 x height cm -> volume -> grams,
with low/high range and a pick), explicit cooked-weight energy densities; optional power calibration."""
import json, re, math

MODEL = "claude-haiku-5-5"
PROMPT = """Overhead photo of food in a cafeteria plate, bowl or container. Estimate each item's weight by geometry, not by
what a typical serving would be.

1. Identify the container and its inner diameter in cm (dinner plate ~26, side plate ~20, bowl ~15, small cup ~9;
   use the visible size of utensils, fruit or packaging as extra cues). Its area is pi*(d/2)^2 cm2.
2. For each food item: the fraction of the container area it covers, its average thickness in cm
   (a scattered layer of leaves ~1 cm but mostly air; a mound of rice 2-4 cm; a single slice of meat ~1 cm),
   then volume = area * thickness and grams = volume * bulk density (leafy greens ~0.1-0.2, chopped vegetables ~0.5,
   rice/pasta/meat ~0.8-1.0, sauces ~1.0 g/cm3).
   Give grams_low and grams_high bracketing the real weight, then your best grams. A few pieces stay a few grams:
   do not round small items up to a serving.
3. kcal_per_100g for the item as served (cooked weight): e.g. cooked rice ~130, cooked chicken breast ~165,
   roasted potatoes ~150, steamed vegetables ~30-40, raw salad greens ~15-20, fruit ~50, scrambled eggs ~150,
   bacon ~500, cheese ~400. Count visible oil, butter or dressing as its own item.
Reply with JSON only:
{"container_cm": <number>, "items": [{"name": "...", "grams_low": <number>, "grams_high": <number>, "grams": <number>, "kcal_per_100g": <number>}]}"""
A, B, REF = 1.0, 1.0, 300.0


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium"))["items"]
    g_tot = k_tot = 0.0
    for i in items:
        g = float(i.get("grams") or 0)
        lo, hi = float(i.get("grams_low") or g), float(i.get("grams_high") or g)
        if lo > 0 and hi > 0 and g > 0:
            g = math.exp((math.log(lo) + math.log(hi) + math.log(g)) / 3)
        g_tot += g
        k_tot += g * float(i["kcal_per_100g"]) / 100
    return {"kcal": A * REF * (max(k_tot, 1.0) / REF) ** B, "mass_g": g_tot}
