"""Comparator (Nakagawa & Yamamoto 2026 style): the single-image direct prompt on the before photo and on the after photo,
eaten = before − after (floored at 0). Same prompt text as the single-image baseline, so the before call is a cache hit."""
import json, re

MODEL = "gpt-6-astra"
PROMPT = """This is a photo of a meal. Estimate the total food energy of everything on the plate.
Reply with JSON only: {"kcal": <number>, "mass_g": <total grams of food>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate2(before, after, llm):
    b = float(parse(llm.ask(PROMPT, before, model=MODEL, effort="low"))["kcal"])
    a = float(parse(llm.ask(PROMPT, after, model=MODEL, effort="low"))["kcal"])
    return {"kcal": max(b - a, 0.0), "served_kcal": b, "leftover_kcal": a}
