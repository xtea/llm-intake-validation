"""Ensemble v4 (single view, for analysis): h0 direct prompt at medium effort."""
import json, re

MODEL = "claude-haiku-5-5"
PROMPT = """This is a photo of a meal. Estimate the total food energy of everything on the plate.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate(image, llm):
    return parse(llm.ask(PROMPT, image, model=MODEL, effort="medium"))
