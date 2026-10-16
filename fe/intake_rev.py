"""Addendum H, v0.1 review analyses (post hoc, exploratory; offline). python3 -m fe.intake_rev > results/intake_rev.txt

R1  Between-model differences on the same 802 meals as Table 2 (point estimate from the sample; bootstrap for CI only).
R3  Fixed eaten-fraction baseline: before-only estimate × c, c = Σ eaten / Σ served over OTHER participants' meals
    (leave-one-participant-out; rule fixed before computing). Compared with both photos (meal MAE%, day mean, LoA,
    within 800 kJ; paired participant bootstrap) and share-eaten error of c vs the model's own share.
R4  Leftover effect modification on the kcal scale: d = |both − eaten| − |before − eaten| per meal.
R5  Excluding the 100 pilot meals (and, stricter, all pilot participants).
R10 Failure handling: valid-output subset sensitivity.
"""
import json, os, random, statistics as st
from fe.llm import ROOT
from fe.intake_report import LAB, MODELS, scored, mae, bias, days, day_stats, B, KJ800
from fe.intake import subset

ITS = sorted(LAB)
KNOWN = [i for i in ITS if LAB[i]["served_kcal"]]
LEFT = {i for i in KNOWN if 1 - LAB[i]["kcal"] / LAB[i]["served_kcal"] >= .1}


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


E = {m: (scored(s)[0], scored(d)[0]) for m, (s, d, _) in MODELS.items()}


def r1():
    print("## R1. Δ MAE% (both − before) per model and minus Haiku 5.5, all 802 meals\n")
    print("| Model | Δ [95% CI] | Δ − Δ Haiku [95% CI] |")
    print("|---|---|---|")
    bs = pboot(ITS, 21)
    hs, hd = E["Haiku 5.5"]
    dh = lambda its: mae(hd, its) - mae(hs, its)
    for m, (es, ed) in E.items():
        d = lambda its: mae(ed, its) - mae(es, its)
        v1 = [d(b) for b in bs]
        if m == "Haiku 5.5":
            print(f"| {m} | {f(d(ITS), v1)} | — |")
        else:
            print(f"| {m} | {f(d(ITS), v1)} | {f(d(ITS) - dh(ITS), [d(b) - dh(b) for b in bs])} |")


def r3():
    print("\n## R3. Fixed eaten-fraction baseline (leave-one-participant-out c = Σ eaten / Σ served of other participants)\n")
    parts = sorted({LAB[i]["participant"] for i in ITS})
    tot_e = {p: sum(LAB[i]["kcal"] for i in KNOWN if LAB[i]["participant"] == p) for p in parts}
    tot_s = {p: sum(LAB[i]["served_kcal"] for i in KNOWN if LAB[i]["participant"] == p) for p in parts}
    TE, TS = sum(tot_e.values()), sum(tot_s.values())
    c = {p: (TE - tot_e[p]) / (TS - tot_s[p]) for p in parts}
    print(f"c ranges {min(c.values()):.3f}–{max(c.values()):.3f} (pooled {TE / TS:.3f})\n")
    ae_c = st.mean(abs(c[LAB[i]['participant']] - LAB[i]['kcal'] / LAB[i]['served_kcal']) for i in KNOWN) * 100
    print(f"share-eaten absolute error of the constant: {ae_c:.1f} points (meals with served defined, n={len(KNOWN)})\n")
    dd = days()
    parts_d = {}
    for k in dd:
        parts_d.setdefault(k[0], []).append(k)
    pk = sorted(parts_d)
    rng = random.Random(31)
    bsd = [[k for p in (rng.choice(pk) for _ in pk) for k in parts_d[p]] for _ in range(B)]
    bs = pboot(ITS, 32)
    bl = pboot(sorted(LEFT), 33)
    print("| Model | MAE% before×c | MAE% both | Δ both − before×c, all [CI] | Δ, ≥10% left [CI] | Day mean %: before×c / both | "
          "Day LoA: before×c / both | Within 800 kJ %: before×c / both |")
    print("|---|---|---|---|---|---|---|---|")
    for m, (es, ed) in E.items():
        ec = {i: es[i] * c[LAB[i]["participant"]] for i in ITS}
        d = lambda its: mae(ed, its) - mae(ec, its)
        a, b_ = day_stats(ec, dd), day_stats(ed, dd)
        print(f"| {m} | {mae(ec, ITS):.1f} | {mae(ed, ITS):.1f} | {f(d(ITS), [d(x) for x in bs])} | "
              f"{f(d(sorted(LEFT)), [d(x) for x in bl])} | {a[0]:+.1f} / {b_[0]:+.1f} | {a[1]:+.0f}..{a[2]:+.0f} / {b_[1]:+.0f}..{b_[2]:+.0f} | "
              f"{a[3]:.0f} / {b_[3]:.0f} |")


def r4():
    print("\n## R4. Leftover effect modification in kcal: d = |both − eaten| − |before − eaten| (kcal per meal)\n")
    print("| Model | mean d, ≥10% left [CI] | mean d, <10% left [CI] | difference [CI] |")
    print("|---|---|---|---|")
    bs = pboot(KNOWN, 41)
    for m, (es, ed) in E.items():
        dm = lambda its: st.mean(abs(ed[i] - LAB[i]["kcal"]) - abs(es[i] - LAB[i]["kcal"]) for i in its)
        L = lambda b: [i for i in b if i in LEFT]
        M = lambda b: [i for i in b if i not in LEFT]
        vl, vm, vd = [], [], []
        for b in bs:
            a_, c_ = dm(L(b)), dm(M(b))
            vl.append(a_); vm.append(c_); vd.append(a_ - c_)
        a0, c0 = dm(L(KNOWN)), dm(M(KNOWN))
        print(f"| {m} | {f(a0, vl)} | {f(c0, vm)} | {f(a0 - c0, vd)} |")


def r5():
    lab_list = json.load(open(os.path.join(ROOT, "data", "labels", "acetada_intake.json")))
    pilot = {l["item"] for l in subset("pilot", lab_list)}
    pilot_p = {LAB[i]["participant"] for i in pilot}
    for name, keep in (("excluding 100 pilot meals", [i for i in ITS if i not in pilot]),
                       ("excluding all pilot participants", [i for i in ITS if LAB[i]["participant"] not in pilot_p])):
        dd = {k: v for k, v in days().items() if all(i in set(keep) for i in v)}
        print(f"\n## R5. {name}: {len(keep)} meals, {len({LAB[i]['participant'] for i in keep})} participants, {len(dd)} complete days\n")
        print("| Model | MAE% before → both (Δ) | Δ ≥10% left | Day mean % both | Day LoA both |")
        print("|---|---|---|---|---|")
        lk = [i for i in keep if i in LEFT]
        for m, (es, ed) in E.items():
            mu, lo, hi, _ = day_stats(ed, dd)
            print(f"| {m} | {mae(es, keep):.1f} → {mae(ed, keep):.1f} ({mae(ed, keep) - mae(es, keep):+.1f}) | "
                  f"{mae(ed, lk) - mae(es, lk):+.1f} | {mu:+.1f} | {lo:+.0f}..{hi:+.0f} |")


def r10():
    print("\n## R10. Valid-output subset (meals where all three conditions parsed for that model)\n")
    print("| Model | n | MAE% before / subtraction / both | bias % both |")
    print("|---|---|---|---|")
    for m, (s, d, sb) in MODELS.items():
        ok = set(scored(s)[1]) & set(scored(d)[1]) & set(scored(sb)[1])
        its = [i for i in ITS if i in ok]
        es, ed, eb = scored(s)[0], scored(d)[0], scored(sb)[0]
        print(f"| {m} | {len(its)} | {mae(es, its):.1f} / {mae(eb, its):.1f} / {mae(ed, its):.1f} | {bias(ed, its):+.1f} |")


if __name__ == "__main__":
    r1(); r3(); r4(); r5(); r10()
