"""den_v3: h2 portion logic + identification rules + visual (not assumed) hidden-fat rules."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl.
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


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    for s in range(3):
        try:
            items = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium", sample=s))["items"]
            grams = sum(float(i["grams"]) for i in items)
            kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
            return {"kcal": kcal, "mass_g": grams}
        except (ValueError, KeyError, AttributeError, TypeError):
            continue
    raise ValueError("no json")
