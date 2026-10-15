"""den_v1: h2 portion logic + explicit identification and hidden-fat (energy density) rules."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.

Energy density (kcal per 100 g) must match the item AS SERVED (cooked state, with absorbed fat):
- Identify carefully. A pile of fluffy white curds is scrambled egg whites (~55) or scrambled eggs (~150), not feta.
  Dark glossy oval pieces are olives (~120-145), not dates. Orange cubes are sweet potato or squash (~90), not cheese.
  Grains/rice/pasta are cooked (rice ~130, quinoa ~120, pasta ~150), never dry values.
- Hidden fat: prepared food is almost always cooked or dressed with oil even when you cannot see it.
  Leafy salads and raw-vegetable salads: add a separate item "vinaigrette" weighing about 12% of the salad,
  at 600 kcal/100 g. Roasted or sauteed vegetables: use ~70-100 instead of the raw value (oil included).
  Glossy or shiny food: add oil. Visible sauce, butter, cheese or dressing: add as its own item.
- Reference values: leafy greens 20, raw vegetables 25-40, fruit 50-70, potato roasted 130, fries 300,
  chicken breast 165, beef/pork cooked 220-270, bacon 500, fish 140-200, tofu 80-140, beans/chickpeas 140,
  egg 150, cheese 350-400, bread 260, pizza 270, nuts 600, oil 884.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    items = parse(llm.ask(PROMPT, image, model=MODEL, effort="medium"))["items"]
    grams = sum(float(i["grams"]) for i in items)
    kcal = sum(float(i["grams"]) * float(i["kcal_per_100g"]) / 100 for i in items)
    return {"kcal": kcal, "mass_g": grams}
