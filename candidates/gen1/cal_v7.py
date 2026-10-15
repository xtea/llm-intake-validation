"""cal_v7: two-view ensemble with post-hoc log-linear calibration (systematic-bias correction).

View 1: plain direct-total prompt (h0) sampled K=5 at low effort, geometric mean  -> d
View 2: geometric decomposition prompt (cal_v3: container cm -> area x thickness -> grams, low/high/best) -> g
kcal = REF * exp(C + WD*log(d/REF) + WG*log(g/REF))
Constants fitted by Nelder-Mead minimising sum|est-true| (= mae_pct_of_mean) on the search-300 rows of the
UNCALIBRATED runs runs/cal_v4/search-300.json and runs/cal_v3/search-300.json (search split only).
Fallback when view 2 fails: kcal = REF * exp(C1 + W1*log(d/REF)), fitted the same way on cal_v4 alone.
WD+WG = 0.85 < 1: shrinks toward the middle, undoing the over-dispersed totals (big plates over-, tiny under-shrunk).
"""
import json, re, math

MODEL = "claude-haiku-5-5"
PROMPT_DIRECT = """This is a photo of a meal. Estimate the total food energy of everything on the plate.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""
PROMPT_GEOM = """Overhead photo of food in a cafeteria plate, bowl or container. Estimate each item's weight by geometry, not by
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
K = 5
REF = 300.0
C, WD, WG = -0.1558, 0.6489, 0.1994
C1, W1 = -0.2699, 0.8551


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def gmean(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


def direct(image, llm):
    ks, ms = [], []
    for s in range(K):
        try:
            d = parse(llm.ask(PROMPT_DIRECT, image, model=MODEL, effort="low", sample=s))
            k, m = float(d["kcal"]), float(d.get("mass_g") or 0)
        except Exception:
            continue
        if k > 0:
            ks.append(k)
            if m > 0:
                ms.append(m)
    return gmean(ks), (gmean(ms) if ms else None)


def geometric(image, llm):
    items = parse(llm.ask(PROMPT_GEOM, image, model=MODEL, effort="medium"))["items"]
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
    d, dm = direct(image, llm)
    try:
        g, gm = geometric(image, llm)
    except Exception:
        g, gm = 0.0, 0.0
    if g > 0:
        kcal = REF * math.exp(C + WD * math.log(d / REF) + WG * math.log(g / REF))
    else:
        kcal = REF * math.exp(C1 + W1 * math.log(d / REF))
    return {"kcal": kcal, "mass_g": dm or gm or None}
