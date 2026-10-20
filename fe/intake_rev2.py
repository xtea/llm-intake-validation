"""Addendum H, v0.2 review analyses (post hoc, exploratory; offline). python3 -m fe.intake_rev2 > results/intake_rev2.txt

S1  Day-level LoA for repeated measures (Bland & Altman 2007, one-way ANOVA with unequal group sizes) and the
    within-participant ICC of e_day; also LoA on the log scale (ratio limits).
S2  Shrinkage check: slope of log(estimate) on log(true) at meal and day level (slope < 1 = shrinkage toward a typical meal).
S3  Q2 as heterogeneity: bootstrap of the range and SD of the models' Δ; all pairwise differences (unadjusted).
S4  Protein under-estimate vs meal composition: Spearman of per-meal protein % error with (a) share of energy from
    animal-source items, (b) protein density (g per 100 kcal).
S5  Sanity check vs Coburn et al. 2025: per-meal MAE kcal and MAPE of the before-only condition.
"""
import csv, math, os, random, statistics as st
import numpy as np
from fe.llm import ROOT
from fe.intake_report import LAB, MODELS, scored, mae, days, B

ITS = sorted(LAB)
ANIMAL = ("chicken", "beef", "salmon", "ham", "egg", "cheese", "yog", "milk", "lasagna", "ricotta", "sushi", "tuna", "fish",
          "lamb", "pork", "turkey", "prawn", "flat white", "cappuccino")  # clearly animal-protein items; mixed dishes excluded


def spearman(x, y):
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def rm_loa(e_by_part):
    """Bland & Altman 2007, section 3 (true value varies within subject): LoA = mean ± 1.96 * sqrt(s_b^2 + s_w^2)."""
    groups = [v for v in e_by_part.values() if v]
    n = len(groups)
    allv = [x for g in groups for x in g]
    N = len(allv)
    gm = st.mean(allv)
    ssb = sum(len(g) * (st.mean(g) - gm) ** 2 for g in groups)
    ssw = sum((x - st.mean(g)) ** 2 for g in groups for x in g)
    msb, msw = ssb / (n - 1), ssw / (N - n)
    m0 = (N - sum(len(g) ** 2 for g in groups) / N) / (n - 1)
    s2_b = max((msb - msw) / m0, 0.0)
    s2_w = msw
    sd = math.sqrt(s2_b + s2_w)
    icc = s2_b / (s2_b + s2_w) if s2_b + s2_w > 0 else 0.0
    return gm, gm - 1.96 * sd, gm + 1.96 * sd, icc, math.sqrt(s2_w)


def s1():
    dd = days()
    print(f"## S1. Day-level agreement, both photos: naive LoA vs repeated-measures LoA (Bland & Altman 2007); {len(dd)} days\n")
    print("| Model | mean e_day % | naive LoA | RM LoA | within-participant SD | ICC | log-scale ratio LoA (est/true) |")
    print("|---|---|---|---|---|---|---|")
    for m, (_, d, _) in MODELS.items():
        est = scored(d)[0]
        by, logs = {}, {}
        for (p, _), its in dd.items():
            t = sum(LAB[i]["kcal"] for i in its)
            e = sum(est[i] for i in its)
            by.setdefault(p, []).append((e - t) / t * 100)
            logs.setdefault(p, []).append(math.log(e / t))
        allv = [x for v in by.values() for x in v]
        mu, sd = st.mean(allv), st.stdev(allv)
        gm, lo, hi, icc, sw = rm_loa(by)
        lg = rm_loa(logs)
        print(f"| {m} | {mu:+.1f} | {mu - 1.96 * sd:+.0f} to {mu + 1.96 * sd:+.0f} | {lo:+.0f} to {hi:+.0f} | {sw:.1f} | {icc:.2f} | "
              f"×{math.exp(lg[1]):.2f} to ×{math.exp(lg[2]):.2f} (mean ×{math.exp(lg[0]):.2f}) |")
    print("\nParticipants contribute 1–3 days; the RM method partitions the variance into between- and within-participant parts.")


def s2():
    dd = days()
    print("\n## S2. Shrinkage: OLS slope of log(estimate) on log(true energy), both photos (slope 1 = no shrinkage)\n")
    print("| Model | meal-level slope | day-level slope | day: % error change per doubling of true intake |")
    print("|---|---|---|---|")
    for m, (_, d, _) in MODELS.items():
        est = scored(d)[0]
        x = np.log([LAB[i]["kcal"] for i in ITS]); y = np.log([max(est[i], 1) for i in ITS])
        bm = np.polyfit(x, y, 1)[0]
        xd = np.log([sum(LAB[i]["kcal"] for i in v) for v in dd.values()])
        yd = np.log([sum(est[i] for i in v) for v in dd.values()])
        bd = np.polyfit(xd, yd, 1)[0]
        pe = [(math.exp(b) - math.exp(a)) / math.exp(a) * 100 for a, b in zip(xd, yd)]
        bp = np.polyfit(xd / math.log(2), pe, 1)[0]
        print(f"| {m} | {bm:.2f} | {bd:.2f} | {bp:+.1f} pts |")


def s3():
    print(f"\n## S3. Q2 as heterogeneity of Δ MAE% (both − before) across the {len(MODELS)} models, 802 meals\n")
    rng = random.Random(51)
    g = {}
    for i in ITS:
        g.setdefault(LAB[i]["participant"], []).append(i)
    pk = sorted(g)
    E = {m: (scored(s)[0], scored(d)[0]) for m, (s, d, _) in MODELS.items()}
    def deltas(its):
        return {m: mae(ed, its) - mae(es, its) for m, (es, ed) in E.items()}
    d0 = deltas(ITS)
    rng_, sd_ = [], []
    pair = {}
    names = list(E)
    for _ in range(B):
        b = [i for p in (rng.choice(pk) for _ in pk) for i in g[p]]
        db = deltas(b)
        v = list(db.values())
        rng_.append(max(v) - min(v)); sd_.append(st.pstdev(v))
        for a in range(len(names)):
            for c in range(a + 1, len(names)):
                pair.setdefault((names[a], names[c]), []).append(db[names[a]] - db[names[c]])
    v = list(d0.values())
    q = lambda z: (sorted(z)[int(.025 * B)], sorted(z)[int(.975 * B) - 1])
    print(f"range of Δ across models: {max(v) - min(v):.1f} points [95% CI {q(rng_)[0]:.1f}, {q(rng_)[1]:.1f}]; SD of Δ: {st.pstdev(v):.1f} [{q(sd_)[0]:.1f}, {q(sd_)[1]:.1f}]")
    print(f"direction: {sum(x < 0 for x in v)} of {len(v)} models negative (improved); see Table 2 for which CIs exclude 0\n")
    print("| Model A | Model B | Δ_A − Δ_B [95% CI, unadjusted] |")
    print("|---|---|---|")
    for (a, c), vals in pair.items():
        lo, hi = q(vals)
        print(f"| {a} | {c} | {d0[a] - d0[c]:+.1f} [{lo:+.1f}, {hi:+.1f}] |")


def s4():
    R = list(csv.DictReader(open(os.path.join(ROOT, "data", "acetada", "ACETADA-release", "ACETADA-HF-dataset.csv"))))
    by_path = {}
    for l in LAB.values():
        pass
    # map items back to CSV rows via acetada_intake labels (participant+date+meal is unique after cleaning)
    key = {(l["participant"], l["date"], l["meal"]): i for i, l in LAB.items()}
    comp = {}
    f = lambda v: float(v) if v else 0.0
    for r in R:
        i = key.get((r["participant_id"], r["date"], r["meal_type"]))
        if not i:
            continue
        e_an, e_tot, p_tot = 0.0, 0.0, 0.0
        for k in range(1, int(r["food_item_count"]) + 1):
            n = r[f"food_item_{k}_name"].lower(); e = f(r[f"food_item_{k}_energy_kcal"]); p = f(r[f"food_item_{k}_protein_g"])
            e_tot += e; p_tot += p
            if any(a in n for a in ANIMAL):
                e_an += e
        if e_tot > 0:
            comp[i] = (e_an / e_tot, p_tot / e_tot * 100)
    print(f"\n## S4. Protein error vs meal composition, both photos ({len(comp)} meals)\n")
    print("Animal-source items matched by name keyword (chicken, beef, salmon, ham, egg, cheese, yoghurt, milk, sushi, …).\n")
    print("| Model | protein bias % (total) | Spearman(error %, animal energy share) | Spearman(error %, protein g/100 kcal) | bias: animal share <1/3 / ≥1/3 |")
    print("|---|---|---|---|---|")
    for m, (_, d, _) in MODELS.items():
        rd = scored(d)[1]
        its = [i for i in comp if i in rd and rd[i].get("protein_g") is not None and LAB[i]["protein_g"] > 0]
        err = [(rd[i]["protein_g"] - LAB[i]["protein_g"]) / LAB[i]["protein_g"] * 100 for i in its]
        tot = (sum(rd[i]["protein_g"] for i in its) - sum(LAB[i]["protein_g"] for i in its)) / sum(LAB[i]["protein_g"] for i in its) * 100
        lo_ = [i for i in its if comp[i][0] < 1 / 3]; hi_ = [i for i in its if comp[i][0] >= 1 / 3]
        bb = lambda xs: (sum(rd[i]["protein_g"] for i in xs) - sum(LAB[i]["protein_g"] for i in xs)) / sum(LAB[i]["protein_g"] for i in xs) * 100
        print(f"| {m} | {tot:+.1f} | {spearman(err, [comp[i][0] for i in its]):+.2f} | {spearman(err, [comp[i][1] for i in its]):+.2f} | "
              f"{bb(lo_):+.0f} (n={len(lo_)}) / {bb(hi_):+.0f} (n={len(hi_)}) |")


def s5():
    print("\n## S5. Before-only condition, per-meal MAE (kcal) and MAPE, for comparison with Coburn et al. 2025 Table II\n")
    print("Coburn 2025 (before photos, baseline prompt, consumed labels, 806 meals): closed models calorie MAE 166–211 kcal, MAPE 23–34%.\n")
    print("| Model | MAE kcal | MAPE % | median APE % |")
    print("|---|---|---|---|")
    for m, (s, _, _) in MODELS.items():
        _, rs, _ = scored(s)
        its = [i for i in ITS if i in rs]
        ae = [abs(rs[i]["est"] - LAB[i]["kcal"]) for i in its]
        ape = [a / LAB[i]["kcal"] * 100 for a, i in zip(ae, its)]
        print(f"| {m} | {st.mean(ae):.0f} | {st.mean(ape):.1f} | {st.median(ape):.1f} |")


if __name__ == "__main__":
    s1(); s2(); s3(); s4(); s5()
