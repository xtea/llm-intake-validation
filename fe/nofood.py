"""Image-only hygiene: flag photos that contain no food (e.g. an empty rig or a phone).
Uses only the image, never labels, and is applied to every split alike.
Writes data/exclude_nofood.json (list of item ids). Usage: python3 -m fe.nofood
"""
import glob, json, os
from concurrent.futures import ThreadPoolExecutor
from fe.llm import LLM, ROOT

PROMPT = ("Look at this photo. Is there any food or drink in it (on a plate, in a bowl, or anywhere)? "
          "Answer with exactly one word: FOOD or NOFOOD.")


def main():
    llm = LLM(max_usd=3)
    paths = sorted(glob.glob(os.path.join(ROOT, "data", "images", "*.png")))

    def check(p):
        a = llm.ask(PROMPT, open(p, "rb").read(), model="claude-haiku-5-5", effort="low", max_tokens=1000)
        a2 = None
        if "NOFOOD" in a.upper():  # confirm with a second sample before excluding
            a2 = llm.ask(PROMPT, open(p, "rb").read(), model="claude-haiku-5-5", effort="medium", max_tokens=2000, sample=1)
        return os.path.basename(p)[:-4], a, a2

    with ThreadPoolExecutor(24) as ex:
        res = list(ex.map(check, paths))
    bad = [i for i, a, a2 in res if "NOFOOD" in a.upper() and a2 and "NOFOOD" in a2.upper()]
    json.dump(bad, open(os.path.join(ROOT, "data", "exclude_nofood.json"), "w"), indent=1)
    labs = {}
    for f in glob.glob(os.path.join(ROOT, "data", "labels", "*.json")):
        for l in json.load(open(f)):
            labs[l["item"]] = os.path.basename(f)[:-5]
    from collections import Counter
    print(len(paths), "images;", len(bad), "no-food:", dict(Counter(labs.get(b, "?") for b in bad)), "usd", round(llm.usd, 3))


if __name__ == "__main__":
    main()
