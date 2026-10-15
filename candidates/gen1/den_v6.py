"""den_v6: den_v5 with a second sample of prompt B; ensemble of density-aware prompts (den_v3: visual fat rules; den_v4: flagged raw greens
get deterministic dressing oil), averaged. Portion logic is h2's."""
import json, re, statistics

MODEL = "claude-haiku-5-5"
OIL_FRAC = 0.09  # dressing oil per gram of raw leafy greens (prompt B)
SCALE = 1.0      # global calibration of mass (and so kcal)
SAMPLES_B = 2

PROMPT_A = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.

Then give kcal per 100 g for each item as served:
- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);
  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are
  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.
- Fat: judge from the photo. Leaves or vegetables that look glossy, wet or coated are dressed: add a separate
  "dressing/oil" item of about 5% of their weight at 700 kcal/100 g. Dry, matte leaves get no dressing.
  Cooked vegetables are 25-50 unless visibly oily. Visible sauce, butter, cheese or oil: add as its own item.
- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,
  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,
  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

PROMPT_B = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.

Then give kcal per 100 g for each item as served:
- Identify carefully. A large pile of soft white curds or crumbles is scrambled egg whites (55 kcal/100 g);
  feta only appears as a light sprinkle. Yellow fluffy curds are scrambled eggs (150). Dark glossy ovals are
  olives (130), not dates. Orange cubes are sweet potato or squash (90). Rice, grains and pasta are cooked values.
- Fat: raw leafy greens (lettuce, mixed greens, arugula, spinach, kale, chard) get "greens": true; their
  dressing is added automatically, so do not list a dressing for them. Cooked vegetables are 25-50 and get no
  oil item unless oil is visibly pooled. Other visible sauce, butter, cheese or oil: add as its own item.
- Reference values: leafy greens 20, vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150,
  roasted potato 130, fries 300, chicken breast 165, beef or pork 220-270, sausage 300, bacon 500,
  fish 140-200, tofu 100, beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>, "greens": <true|false>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def run(llm, prompt, image, sample, greens_oil):
    for s in (sample, sample + 10, sample + 20):
        try:
            items = parse(llm.ask(prompt, image, model=MODEL, effort="medium", sample=s))["items"]
            grams = sum(float(i["grams"]) for i in items)
            kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
            oil = greens_oil * sum(float(i["grams"]) for i in items if i.get("greens") is True)
            return kcal + oil * 8.84, grams + oil
        except (ValueError, KeyError, AttributeError, TypeError):
            continue
    return None


def estimate(image, llm):
    outs = [run(llm, PROMPT_A, image, 0, 0.0)]
    outs += [run(llm, PROMPT_B, image, s, OIL_FRAC) for s in range(SAMPLES_B)]
    outs = [o for o in outs if o]
    if not outs:
        raise ValueError("no json")
    kcal = statistics.mean(o[0] for o in outs)
    mass = statistics.mean(o[1] for o in outs)
    return {"kcal": SCALE * kcal, "mass_g": SCALE * mass}
