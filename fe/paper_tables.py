"""Markdown tables for the paper, computed from runs/ (no model calls).

python3 -m fe.paper_tables > results/paper_tables.md
"""
import json, math, os, random
from fe.llm import ROOT
from fe.ablation import MODELS, rows, fit, apply, invert

B = 2000
SYS = {  # model -> (direct, plate, harness A)
    m: (b0, b2, a) for m, (b0, b2, a, _) in MODELS.items()
}


def labels(split):
    return {l["item"]: l for l in json.load(open(os.path.join(ROOT, "data", "labels", f"{split}.json")))}


def est_of(run, split):
    r = rows(run, f"{split}-all")
    return {i: x["est"] for i, x in r.items()} if r else None


def all_rows(run, split):
    p = os.path.join(ROOT, "runs", run, f"{split}-all.json")
    return json.load(open(p))["rows"] if os.path.exists(p) else None


def scored(run, split, lab):
    """est per item; failures scored as the system's own worst relative error (evaluator rule)."""
    rr = all_rows(run, split)
    if rr is None:
        return None
    ok = [r for r in rr if r.get("est") and r["kcal"] > 0]
    worst = max(abs(r["est"] - r["kcal"]) / r["kcal"] for r in ok)
    return {r["item"]: (r["est"] if r.get("est") else r["kcal"] * (1 + worst)) for r in rr}


def mae(est, lab, its):
    return sum(abs(est[i] - lab[i]["kcal"]) for i in its) / sum(lab[i]["kcal"] for i in its) * 100


def boots(lab, its, seed=0):
    rng = random.Random(seed)
    plates = {}
    for i in its:
        plates.setdefault(lab[i]["plate"], []).append(i)
    pk = sorted(plates)
    return [[i for p in (rng.choice(pk) for _ in pk) for i in plates[p]] for _ in range(B)]


def ci(vals):
    v = sorted(vals)
    return v[int(.025 * B)], v[int(.975 * B)]


def cost(run, split):
    p = os.path.join(ROOT, "runs", run, f"{split}-all.json")
    m = json.load(open(p))["metrics"]
    if m.get("cache_hits", 0) > m.get("calls", 0):
        return None
    return m["usd"] / m["n"]


def main_table(split, title, include=("direct", "plate", "A")):
    lab = labels(split)
    systems = []
    for model, (b0, b2, a) in SYS.items():
        for kind, run in zip(("direct", "plate", "A"), (b0, b2, a)):
            if kind in include:
                e = scored(run, split, lab)
                if e:
                    systems.append((model, kind, run, e))
    common = sorted(set.intersection(*[set(e) for *_, e in systems]))
    bs = boots(lab, common)
    ref = [e for m, k, r, e in systems if m == "Haiku 5.5" and k == "A"]
    ref = ref[0] if ref else None
    name = {"direct": "Direct", "plate": "Plate-as-ruler", "A": "Harness A"}
    out = [f"**{title}** ({len(common)} dishes)", "",
           "| Model | System | MAE % [95% CI] | MPE % | MAE kcal | r | vs Haiku A, pts [95% CI] |", "|---|---|---|---|---|---|---|"]
    for model, kind, run, e in systems:
        v = mae(e, lab, common)
        lo, hi = ci(mae(e, lab, b) for b in bs)
        pos = [i for i in common if lab[i]["kcal"] > 0 and e[i] > 0]   # MPE and r undefined for a 0-kcal label (n5k_side has one)
        mpe = sum((e[i] - lab[i]["kcal"]) / lab[i]["kcal"] for i in pos) / len(pos) * 100
        mk = sum(abs(e[i] - lab[i]["kcal"]) for i in common) / len(common)
        r = _corr([math.log(e[i]) for i in pos], [math.log(lab[i]["kcal"]) for i in pos])
        if ref is not None and not (model == "Haiku 5.5" and kind == "A"):
            dl, dh = ci(mae(e, lab, b) - mae(ref, lab, b) for b in bs)
            d = f"{v - mae(ref, lab, common):+.1f} [{dl:+.1f}, {dh:+.1f}]"
        else:
            d = "—"
        bold = "**" if (model == "Haiku 5.5" and kind == "A") else ""
        out.append(f"| {bold}{model}{bold} | {bold}{name[kind]}{bold} | {bold}{v:.1f} [{lo:.1f}, {hi:.1f}]{bold} | {mpe:+.1f} | {mk:.0f} | {r:.3f} | {d} |")
    return "\n".join(out)


def _corr(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def ablation_table(splits):
    out = ["| Model | Split | Direct | Direct + cal | Plate | Plate + cal | A without cal | A |", "|---|---|---|---|---|---|---|---|"]
    for model, (b0, b2, a, (ca, wa)) in MODELS.items():
        for split in splits:
            lab = labels(split)
            cells = []
            for run in (b0, b2):
                e = est_of(run, split)
                f0 = rows(run, "search-300-f0")
                if e and f0:
                    C, W = fit(list(f0.values()))
                    its = list(e)
                    cells += [f"{mae(e, lab, its):.1f}", f"{mae({i: apply(C, W, x) for i, x in e.items()}, lab, its):.1f}"]
                else:
                    cells += ["–", "–"]
            ea = est_of(a, split)
            if ea:
                its = list(ea)
                cells += [f"{mae({i: invert(ca, wa, x) for i, x in ea.items()}, lab, its):.1f}", f"{mae(ea, lab, its):.1f}"]
            else:
                cells += ["–", "–"]
            if any(c != "–" for c in cells):
                out.append(f"| {model} | {split} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def config_table():
    cfg = [
        ("Haiku 5.5", "claude-haiku-5-5", "Direct", 1, "low", "—"),
        ("Haiku 5.5", "claude-haiku-5-5", "Plate-as-ruler", 1, "medium", "—"),
        ("Haiku 5.5", "claude-haiku-5-5", "Harness A", 6, "low/medium", "C=−0.074, W=0.930 (search)"),
        ("Haiku 5.5", "claude-haiku-5-5", "Harness A-v2", 6, "low/medium", "6 constants (search)"),
        ("Haiku 5.5", "claude-haiku-5-5", "Harness B", 3, "low/medium", "none"),
        ("Haiku 5.5", "claude-haiku-5-5", "Harness C", 2, "low/medium", "C=−0.120, two weights (search)"),
        ("Sonnet 5.5", "claude-sonnet-5-5", "Harness A", 6, "low/medium", "C=−0.04, W=0.87 (fold 0)"),
        ("Opus 5.5", "claude-opus-5-5", "Harness A", 6, "low/medium", "C=−0.12, W=0.945 (fold 0)"),
        ("GPT-6 luna", "gpt-6-luna", "Harness A", 6, "low/medium", "C=−0.035, W=0.855 (fold 0)"),
        ("GPT-6.1 sol", "gpt-6.1-sol", "Harness A", 6, "low/medium", "C=−0.27, W=1.02 (fold 0)"),
        ("GPT-6 astra", "gpt-6-astra", "Harness A", 6, "low/medium", "C=−0.27, W=0.99 (fold 0)"),
    ]
    out = ["| Model | API id | System | Calls/dish | Effort | Fitted constants (data) |", "|---|---|---|---|---|---|"]
    out += [f"| {a} | `{b}` | {c} | {d} | {e} | {f} |" for a, b, c, d, e, f in cfg]
    out.append("")
    out.append("Images: PNG, long side ≤1024 px (Nutrition5k overhead images are 640×480). Claude: Messages API, adaptive thinking with "
               "the stated effort, no temperature setting. GPT: chat completions, image as data URL with detail=high, reasoning_effort "
               "mapped from the stated effort. Prompts are byte-identical across models. Full prompts and code are in the repository.")
    return "\n".join(out)


def failures():
    out = ["| Split | System | Parse failures | Network failures (retried) |", "|---|---|---|---|"]
    import glob
    for split in ("test", "cafe2", "nvreal", "acetada", "n5k_side"):
        for p in sorted(glob.glob(os.path.join(ROOT, "runs", "*", f"{split}-all.json"))):
            rr = json.load(open(p))["rows"]
            pf = sum(1 for r in rr if r.get("error") and not any(k in r["error"] for k in ("Timeout", "Connection")))
            nf = sum(1 for r in rr if r.get("error") and any(k in r["error"] for k in ("Timeout", "Connection")))
            if pf or nf:
                out.append(f"| {split} | {os.path.basename(os.path.dirname(p))} | {pf} | {nf} |")
    return "\n".join(out)


if __name__ == "__main__":
    print("## TEST\n\n" + main_table("test", "Nutrition5k test split (cleaned, overhead)"))
    print("\n## NVREAL\n\n" + main_table("nvreal", "NutritionVerse-Real", include=("direct", "plate", "A")))
    if os.path.exists(os.path.join(ROOT, "runs", "compA_v4", "acetada-all.json")):
        print("\n## ACETADA\n\n" + main_table("acetada", "ACETADA (before photos, served energy)", include=("direct", "plate", "A")))
    print("\n## ABLATION\n\n" + ablation_table(["test", "nvreal"] + (["acetada"] if os.path.exists(os.path.join(ROOT, "runs", "compA_v4", "acetada-all.json")) else [])))
    print("\n## CONFIG\n\n" + config_table())
    print("\n## FAILURES\n\n" + failures())
