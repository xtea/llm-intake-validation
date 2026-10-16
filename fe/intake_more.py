"""Addendum H, outline-review analyses (post hoc, exploratory; offline). python3 -m fe.intake_more > results/intake_more.txt

Leftover definition used throughout: energy left = served energy − consumed energy, whole meal; served energy per item =
consumed energy / consumed grams × grams before eating. Served energy is undefined for meals with an item that was not eaten
at all (energy per gram unknown); those meals are left out of leftover-based analyses only.
"""
import math, random, statistics as st
from fe.intake_report import LAB, MODELS, scored, mae, days, day_stats, B, KJ800
from fe.ablation import fit, apply

ITS = sorted(LAB)
KNOWN = [i for i in ITS if LAB[i]["served_kcal"]]


def mass_vs_energy():
    import csv, os
    from fe.llm import ROOT
    print(f"## Leftover definition\n\nmeals {len(ITS)}; served energy known {len(KNOWN)}; undefined {len(ITS) - len(KNOWN)} "
          "(an item with 0 g eaten)\n")
    fe_ = [1 - LAB[i]["kcal"] / LAB[i]["served_kcal"] for i in KNOWN]
    print(f"energy left fraction: median {st.median(fe_):.3f}; ≥10%: {sum(x >= .1 for x in fe_)}; ≥25%: {sum(x >= .25 for x in fe_)}\n")


def eaten_fraction():
    print("## Eaten fraction from the both-photos answers (served known; predicted = eaten / served from the model's own numbers)\n")
    print("| Model | n | mean predicted − true (pts) | MAE (pts) | Spearman |")
    print("|---|---|---|---|---|")
    from fe.intake_report import spearman
    for m, (_, d, _) in MODELS.items():
        _, rd, _ = scored(d)
        pr = [(r["est"] / r["served_kcal"], LAB[i]["kcal"] / LAB[i]["served_kcal"]) for i, r in rd.items()
              if i in LAB and LAB[i]["served_kcal"] and r.get("served_kcal")]
        pr = [(min(p, 1.5), t) for p, t in pr]
        print(f"| {m} | {len(pr)} | {st.mean(p - t for p, t in pr) * 100:+.1f} | {st.mean(abs(p - t) for p, t in pr) * 100:.1f} | "
              f"{spearman([p for p, _ in pr], [t for _, t in pr]):.2f} |")


def decomposition_kcal():
    print("\n## Decomposition of the before-only error in kcal per meal (served known)\n")
    print("| Model | Mean estimate − served | Mean leftover | Mean estimate − consumed | ≥10% left: meals offset* | median kcal moved toward truth by the offset** |")
    print("|---|---|---|---|---|---|")
    left = [i for i in KNOWN if 1 - LAB[i]["kcal"] / LAB[i]["served_kcal"] >= .1]
    for m, (s, _, _) in MODELS.items():
        es = scored(s)[0]
        a = st.mean(es[i] - LAB[i]["served_kcal"] for i in KNOWN)
        b = st.mean(LAB[i]["served_kcal"] - LAB[i]["kcal"] for i in KNOWN)
        off = [i for i in left if es[i] < LAB[i]["served_kcal"]]
        gain = [abs(es[i] - LAB[i]["served_kcal"]) - abs(es[i] - LAB[i]["kcal"]) for i in off]
        pos = [g for g in gain if g > 0]
        print(f"| {m} | {a:+.0f} | {b:+.0f} | {a + b:+.0f} | {len(pos)}/{len(left)} | {st.median(pos) if pos else 0:.0f} |")
    print("\n*under-estimated served energy and ended closer to consumed than to served. **|est − served| − |est − consumed| among those meals.")


def local_recal(k=20, draws=200):
    print(f"\n## Local recalibration of the both-photos estimates (2 constants on k={k} meals from other participants; {draws} draws)\n")
    print("Metrics on complete feeding days of the remaining participants. 'none' = same days without recalibration.\n")
    print("| Model | MAE% meal: none → cal | Day mean %: none → cal | Day 95% LoA: none → cal | Days within 800 kJ %: none → cal |")
    print("|---|---|---|---|---|")
    dd = days()
    rng = random.Random(5)
    for m, (_, d, _) in MODELS.items():
        ed = scored(d)[0]
        res = []
        for _ in range(draws):
            cal = rng.sample(ITS, k)
            held = {LAB[i]["participant"] for i in cal}
            C, W = fit([{"est": max(ed[i], 1.0), "kcal": LAB[i]["kcal"]} for i in cal])
            e2 = {i: apply(C, W, max(x, 1.0)) for i, x in ed.items()}
            sub = {kk: v for kk, v in dd.items() if kk[0] not in held}
            rest = [i for i in ITS if LAB[i]["participant"] not in held]
            res.append((mae(ed, rest), mae(e2, rest), day_stats(ed, sub), day_stats(e2, sub)))
        f = lambda j: st.mean(r[j] for r in res)
        g = lambda j, t: st.mean(r[j][t] for r in res)
        print(f"| {m} | {f(0):.1f} → {f(1):.1f} | {g(2, 0):+.1f} → {g(3, 0):+.1f} | {g(2, 1):+.0f}..{g(2, 2):+.0f} → {g(3, 1):+.0f}..{g(3, 2):+.0f} | "
              f"{g(2, 3):.0f} → {g(3, 3):.0f} |")


def by_meal():
    print("\n## Both photos: MAE% / bias by meal\n")
    print("| Model | Breakfast | Lunch | Dinner |")
    print("|---|---|---|---|")
    for m, (_, d, _) in MODELS.items():
        ed = scored(d)[0]
        cells = []
        for meal in ("Breakfast", "Lunch", "Dinner"):
            xs = [i for i in ITS if LAB[i]["meal"] == meal]
            b = (sum(ed[i] for i in xs) - sum(LAB[i]["kcal"] for i in xs)) / sum(LAB[i]["kcal"] for i in xs) * 100
            cells.append(f"{mae(ed, xs):.1f} / {b:+.1f} (n={len(xs)})")
        print(f"| {m} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    mass_vs_energy()
    eaten_fraction()
    decomposition_kcal()
    local_recal()
    by_meal()
