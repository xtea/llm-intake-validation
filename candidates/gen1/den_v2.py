"""den_v2: h2 pass for items+grams (portion logic unchanged), then a second image pass that
re-identifies each item and assigns as-served energy density, adding hidden fat (oil, dressing)."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a meal on a plate or in a bowl.
Use the plate or bowl as a ruler: a standard dinner plate is about 26 cm across, a side plate about 20 cm,
a cereal bowl about 15 cm. For each food item, judge its footprint (what fraction of the plate it covers)
and its height, then estimate its weight in grams from that volume. Estimate only what is visible;
do not assume a typical serving. Small amounts (a few leaves, a spoon of rice) must get small weights.
Include oil, dressing or sauce as separate items when you can see them.
Reply with JSON only: {"items": [{"name": "...", "grams": <number>, "kcal_per_100g": <number>}]}"""

DENSITY = """This is an overhead photo of a meal. A first pass listed these items with weights:
%s
Your job is only the energy density side; keep the weights as given.
1. Re-check each item's identity against the photo, for example: a pile of fluffy white curds is usually
   scrambled egg whites (~55 kcal/100 g) or scrambled eggs (~150), rarely feta; dark glossy ovals are olives (~130),
   not dates; orange cubes are sweet potato or squash (~90), not cheese. Grains, rice and pasta are cooked.
2. Give kcal per 100 g for the item as served (cooked state). Use common reference values:
   leafy greens 20, raw vegetables 25-40, fruit 50-70, cooked rice 130, cooked pasta 150, roasted potato 130,
   fries 300, chicken breast 165, beef or pork cooked 220-270, bacon 500, fish 140-200, tofu 100,
   beans or chickpeas 140, egg 150, cheese 350-400, bread 260, pizza 270, nuts 600.
3. Hidden fat: say how many grams of oil, butter or dressing are on or in this item that are not already
   listed as their own item (0 if none). Dressed salads, roasted or sauteed vegetables and pan-cooked
   proteins usually carry a few grams of oil; a plain item (fresh fruit, steamed rice, bread) carries none.
Reply with JSON only: {"items": [{"name": "...", "kcal_per_100g": <number>, "hidden_fat_g": <number>}]}
with one entry per input item, in the same order."""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def ask_json(llm, prompt, image, effort):
    for s in range(3):
        try:
            return parse(llm.ask(prompt, image, model=MODEL, effort=effort, sample=s))["items"]
        except (ValueError, KeyError, AttributeError, TypeError):
            continue
    raise ValueError("no json")


def estimate(image, llm):
    items = ask_json(llm, PROMPT, image, "medium")
    grams = [float(i["grams"]) for i in items]
    listing = "\n".join(f"{k + 1}. {i['name']}: {g:.0f} g" for k, (i, g) in enumerate(zip(items, grams)))
    try:
        dens = ask_json(llm, DENSITY % listing, image, "medium")
        if len(dens) != len(items):
            raise ValueError("length mismatch")
        kcal = 0.0
        fat = 0.0
        for g, d in zip(grams, dens):
            hf = max(0.0, min(float(d.get("hidden_fat_g", 0) or 0), 0.3 * g))
            kcal += g * float(d["kcal_per_100g"]) / 100 + hf * 8.84
            fat += hf
        return {"kcal": kcal, "mass_g": sum(grams) + fat}
    except (ValueError, KeyError, TypeError):
        kcal = sum(g * float(i["kcal_per_100g"]) / 100 for g, i in zip(grams, items))
        return {"kcal": kcal, "mass_g": sum(grams)}
