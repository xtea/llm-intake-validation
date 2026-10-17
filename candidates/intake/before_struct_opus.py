"""Ablation 3b (addendum I): before photo only, structured prompt (same output fields as the both-photos prompt)."""
import json, re

MODEL = "claude-opus-5-5"
PROMPT = """This photo shows a meal before eating. Estimate the food energy that was served, the food energy that will be left over,
and the food energy the person will actually eat (served minus left over). Also estimate the protein, carbohydrate and fat
that the person will actually eat.
Reply with JSON only: {"served_kcal": <number>, "leftover_kcal": <number>, "kcal": <number eaten>, "protein_g": <number>, "carbs_g": <number>, "fat_g": <number>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate2(before, after, llm):
    return parse(llm.ask(PROMPT, before, model=MODEL, effort="low"))
