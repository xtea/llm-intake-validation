"""Direction B: consumed intake from a before photo and an after photo, one call, HIGH reasoning effort (addendum I; prompt identical to dual_direct)."""
import json, re

MODEL = "gpt-6-astra"
PROMPT = """The first photo shows a meal before eating. The second photo shows the same tray after the person finished eating.
Estimate the food energy that was served, the food energy that was left over, and the food energy the person actually ate
(served minus left over). Also estimate the protein, carbohydrate and fat that the person actually ate.
Reply with JSON only: {"served_kcal": <number>, "leftover_kcal": <number>, "kcal": <number eaten>, "protein_g": <number>, "carbs_g": <number>, "fat_g": <number>}"""


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def estimate2(before, after, llm):
    return parse(llm.ask(PROMPT, model=MODEL, effort="high", images=[before, after]))
