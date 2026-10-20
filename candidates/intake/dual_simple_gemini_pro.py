"""Ablation 3a (addendum I): both photos, simple prompt (same output fields as the before-only prompt)."""
import json, re

MODEL = "gemini-4-argon"
PROMPT = """The first photo shows a meal before eating. The second photo shows the same tray after the person finished eating.
Estimate the total food energy the person actually ate.
Reply with JSON only: {"kcal": <number eaten>, "mass_g": <grams of food eaten>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate2(before, after, llm):
    return parse(llm.ask(PROMPT, model=MODEL, effort="low", images=[before, after]))
