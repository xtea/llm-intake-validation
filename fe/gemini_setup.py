"""Addendum J setup. python3 -m fe.gemini_setup <flash_model_id> <pro_model_id> <flash_in> <flash_out> <pro_in> <pro_out>
Writes runs/gemini_prices.json and generates the 12 candidate files by copying the GPT-6 luna candidates with MODEL replaced.
Prompts are therefore byte-identical to the other vendors."""
import json, os, re, sys
from fe.llm import ROOT

CANDS = [("candidates/gpt/b0_direct_gpt_6_luna.py", "candidates/gpt/b0_direct_gemini_{t}.py")] + [
    (f"candidates/intake/{c}_gpt_6_luna.py", f"candidates/intake/{c}_gemini_{{t}}.py")
    for c in ("sub_direct", "dual_direct", "dual_simple", "before_struct", "dual_high")]


def main(flash, pro, fi, fo, pi, po):
    json.dump({flash: [float(fi), float(fo)], pro: [float(pi), float(po)]}, open(os.path.join(ROOT, "runs", "gemini_prices.json"), "w"), indent=1)
    for tier, mid in (("flash", flash), ("pro", pro)):
        for src, dst in CANDS:
            s = open(os.path.join(ROOT, src)).read()
            s2, n = re.subn(r'MODEL = "gpt-6-luna"', f'MODEL = "{mid}"', s)
            assert n == 1, src
            out = os.path.join(ROOT, dst.format(t=tier))
            open(out, "w").write(s2)
            print("wrote", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main(*sys.argv[1:7])
