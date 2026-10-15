"""Ensemble v6 (single view, for analysis): ens_v5 prompt, sample 1: direct total with an explicit plate-ruler and portion audit."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is an overhead photo of a single cafeteria serving on a plate or in a bowl.
Use the dish as a ruler (dinner plate about 26 cm, side plate about 20 cm, bowl about 15 cm).
Think about how much food is really there: many of these servings are small (a few pieces, a thin layer),
and the food energy of small servings is often only 100-300 kcal; a full heaped plate can be 700-1000 kcal.
Estimate the total weight of food you can see and its total food energy, including visible oil or sauce.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    return parse(llm.ask(PROMPT, image, model=MODEL, effort="low", sample=2))
