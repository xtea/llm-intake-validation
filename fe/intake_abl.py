"""Addendum I analysis (exploratory; offline). python3 -m fe.intake_abl > results/intake_abl.txt

A  Photo vs prompt: (1) before only, simple prompt; (3b) before only, structured prompt; (3a) both photos, simple prompt;
   (3) both photos, structured prompt. Photo effect = (3) − (3b) and (3a) − (1); prompt effect = (3b) − (1) and (3) − (3a).
B  Grams eaten from (3a) vs weighed grams eaten (for comparison with DietDelta's PMAE).
C  Test–retest of (3) on the 100 pilot meals: three fresh calls per meal.
D  High vs low reasoning effort for (3) on the 100 pilot meals.
"""
import csv, json, os, random, statistics as st
from fe.llm import ROOT
from fe.intake_report import LAB, MODELS, mae, bias, days, day_stats, B
from fe.intake import subset

ITS = sorted(LAB)
KEY = {"Haiku 5.5": "haiku", "Sonnet 5.5": "sonnet", "Opus 5.5": "opus", "GPT-6 luna": "gpt_6_luna", "GPT-6.1 sol": "gpt_6_1_sol",
       "GPT-6 astra": "gpt_6_astra", "Gemini 3.8 Flash": "gemini_flash", "Gemini 4 Argon": "gemini_pro"}


def load(run, tag):
    p = os.path.join(ROOT, "runs", run, tag + ".json")
    if not os.path.exists(p):
        if tag == "intake-pilot":  # models not in the pilot: their first call on these meals is the full run (same cache key)
            full = load(run, "intake-all")
            return full
        return None
    return {r["item"]: r for r in json.load(open(p))["rows"]}


def scored_rows(rows):
    """failure rule of addendum H applied to an arbitrary row dict"""
    rr = {i: r for i, r in rows.items() if i in LAB}
    ok = {i: r for i, r in rr.items() if r.get("est") is not None and r["est"] >= 0}
    worst = max(abs(r["est"] - LAB[i]["kcal"]) / LAB[i]["kcal"] for i, r in ok.items())
    est = {i: r["est"] for i, r in ok.items()}
    for i in rr:
        if i not in est:
            est[i] = LAB[i]["kcal"] * (1 + worst)
    return est, ok, len(rr) - len(ok)


def pboot(its, seed):
    rng = random.Random(seed)
    g = {}
    for i in its:
        g.setdefault(LAB[i]["participant"], []).append(i)
    pk = sorted(g)
    return [[i for p in (rng.choice(pk) for _ in pk) for i in g[p]] for _ in range(B)]


def ci(v):
    v = sorted(v)
    return v[int(.025 * B)], v[int(.975 * B) - 1]


def f(x, v):
    lo, hi = ci(v)
    return f"{x:+.1f} [{lo:+.1f}, {hi:+.1f}]"


def section_a():
    print("## A. Photo vs prompt (MAE% of mean consumed energy, 802 meals; paired participant bootstrap)\n")
    print("| Model | (1) before, simple | (3b) before, structured | (3a) both, simple | (3) both, structured | photo effect, structured prompt (3)−(3b) | photo effect, simple prompt (3a)−(1) | prompt effect, before only (3b)−(1) | prompt effect, both photos (3)−(3a) | fails 3b/3a |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    bs = pboot(ITS, 61)
    dd = days()
    day_rows = []
    for m, (s1, s3, _) in MODELS.items():
        k = KEY[m]
        r1 = load(s1, "acetada_intake-all"); r3 = load(s3, "intake-all")
        r3a = load(f"dual_simple_{k}", "intake-all"); r3b = load(f"before_struct_{k}", "intake-all")
        if not (r3a and r3b):
            print(f"| {m} | (missing) |"); continue
        e1, _, _ = scored_rows(r1); e3, _, _ = scored_rows(r3)
        e3a, _, fa = scored_rows(r3a); e3b, _, fb = scored_rows(r3b)
        d = lambda ea, eb, its: mae(ea, its) - mae(eb, its)
        cells = [f"{mae(e, ITS):.1f} ({bias(e, ITS):+.1f})" for e in (e1, e3b, e3a, e3)]
        effs = []
        for ea, eb in ((e3, e3b), (e3a, e1), (e3b, e1), (e3, e3a)):
            effs.append(f(d(ea, eb, ITS), [d(ea, eb, b) for b in bs]))
        print(f"| {m} | " + " | ".join(cells) + " | " + " | ".join(effs) + f" | {fb}/{fa} |")
        day_rows.append((m, [day_stats(e, dd) for e in (e1, e3b, e3a, e3)]))
    print("\n### Day level (mean e_day %; 95% LoA; days within 800 kJ %)\n")
    print("| Model | (1) before, simple | (3b) before, structured | (3a) both, simple | (3) both, structured |")
    print("|---|---|---|---|---|")
    for m, ds in day_rows:
        print(f"| {m} | " + " | ".join(f"{mu:+.1f}; {lo:+.0f}..{hi:+.0f}; {w:.0f}" for mu, lo, hi, w in ds) + " |")


def section_b():
    R = list(csv.DictReader(open(os.path.join(ROOT, "data", "acetada", "ACETADA-release", "ACETADA-HF-dataset.csv"))))
    key = {(l["participant"], l["date"], l["meal"]): i for i, l in LAB.items()}
    grams = {}
    for r in R:
        i = key.get((r["participant_id"], r["date"], r["meal_type"]))
        if i and r["total_consumed_g"]:
            grams[i] = float(r["total_consumed_g"])
    print(f"\n## B. Grams eaten, (3a) both photos with the simple prompt ({len(grams)} meals with weighed grams)\n")
    print("DietDelta [6] on ACETADA pairs (grams, closed general model given the true food list): both images in one call PMAE 38.9%; "
          "separate estimates subtracted 38.95%; DietDelta (trained) 14.2%. PMAE = MAE / mean true grams.\n")
    print("| Model | n with mass | MAE g | PMAE % | bias % |")
    print("|---|---|---|---|---|")
    for m in MODELS:
        r = load(f"dual_simple_{KEY[m]}", "intake-all")
        if not r:
            continue
        its = [i for i in grams if i in r and r[i].get("mass_g") and grams[i] > 0]
        ae = [abs(r[i]["mass_g"] - grams[i]) for i in its]
        tot = sum(grams[i] for i in its)
        print(f"| {m} | {len(its)} | {st.mean(ae):.0f} | {sum(ae) / tot * 100:.1f} | {(sum(r[i]['mass_g'] for i in its) - tot) / tot * 100:+.1f} |")


def section_c():
    pilot = sorted(l["item"] for l in subset("pilot", json.load(open(os.path.join(ROOT, "data", "labels", "acetada_intake.json")))))
    print(f"\n## C. Test–retest, (3) both photos, {len(pilot)} pilot meals, three fresh calls\n")
    print("| Model | MAE% run 1 / 2 / 3 | range of MAE% | median per-meal CV % | mean |run i − run j| as % of truth | meals with all 3 parsed |")
    print("|---|---|---|---|---|---|")
    for m, (_, s3, _) in MODELS.items():
        runs = [load(s3, "intake-pilot"), load(s3, "intake-pilot-r1"), load(s3, "intake-pilot-r2")]
        if not all(runs):
            print(f"| {m} | (missing) |"); continue
        ok = [i for i in pilot if all(r.get(i, {}).get("est") for r in runs)]
        maes = [sum(abs(r[i]["est"] - LAB[i]["kcal"]) for i in ok) / sum(LAB[i]["kcal"] for i in ok) * 100 for r in runs]
        cv = [st.stdev([r[i]["est"] for r in runs]) / st.mean([r[i]["est"] for r in runs]) * 100 for i in ok]
        pd = []
        for i in ok:
            v = [r[i]["est"] for r in runs]
            pd += [abs(v[a] - v[b]) / LAB[i]["kcal"] * 100 for a in range(3) for b in range(a + 1, 3)]
        print(f"| {m} | {maes[0]:.1f} / {maes[1]:.1f} / {maes[2]:.1f} | {max(maes) - min(maes):.1f} | {st.median(cv):.1f} | {st.mean(pd):.1f} | {len(ok)}/{len(pilot)} |")


def section_d():
    pilot = sorted(l["item"] for l in subset("pilot", json.load(open(os.path.join(ROOT, "data", "labels", "acetada_intake.json")))))
    print(f"\n## D. Reasoning effort, (3) both photos, {len(pilot)} pilot meals: low vs high\n")
    print("| Model | MAE% low (3 runs, mean) | MAE% high | bias % low / high | USD per meal low / high |")
    print("|---|---|---|---|---|")
    for m, (_, s3, _) in MODELS.items():
        lows = [load(s3, t) for t in ("intake-pilot", "intake-pilot-r1", "intake-pilot-r2")]
        hi = load(f"dual_high_{KEY[m]}", "intake-pilot")
        if not hi or not all(lows):
            print(f"| {m} | (missing) |"); continue
        ok = [i for i in pilot if hi.get(i, {}).get("est") and all(r.get(i, {}).get("est") for r in lows)]
        ml = st.mean(sum(abs(r[i]["est"] - LAB[i]["kcal"]) for i in ok) / sum(LAB[i]["kcal"] for i in ok) * 100 for r in lows)
        mh = sum(abs(hi[i]["est"] - LAB[i]["kcal"]) for i in ok) / sum(LAB[i]["kcal"] for i in ok) * 100
        bl = st.mean((sum(r[i]["est"] for i in ok) - sum(LAB[i]["kcal"] for i in ok)) / sum(LAB[i]["kcal"] for i in ok) * 100 for r in lows)
        bh = (sum(hi[i]["est"] for i in ok) - sum(LAB[i]["kcal"] for i in ok)) / sum(LAB[i]["kcal"] for i in ok) * 100
        cl = json.load(open(os.path.join(ROOT, "runs", s3, "intake-pilot-r1.json")))["metrics"]
        ch = json.load(open(os.path.join(ROOT, "runs", f"dual_high_{KEY[m]}", "intake-pilot.json")))["metrics"]
        print(f"| {m} | {ml:.1f} | {mh:.1f} | {bl:+.1f} / {bh:+.1f} | {cl['usd'] / max(cl['calls'], 1):.4f} / {ch['usd'] / max(ch['calls'], 1):.4f} |")


if __name__ == "__main__":
    section_a(); section_b(); section_c(); section_d()
