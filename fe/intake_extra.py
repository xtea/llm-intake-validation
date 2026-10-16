"""Addendum H, review-driven analyses (post hoc, exploratory; offline). python3 -m fe.intake_extra > results/intake_extra.txt

1. Paired change (both photos − before only) in meals with ≥10% energy left vs mostly eaten (<10% left), and the
   difference between the two (bootstrap by participant). The 10% cut point was pre-registered (addendum H).
2. Decomposition of the before-only error vs consumed energy into (estimate − served) + (served − consumed), per model,
   on meals where served energy is known; same-meal offset check.
3. Between-model heterogeneity: improvement of each model minus Haiku's, with CI.
4. Equivalence-style check of the day-level mean error: 90% CI within ±10%.
"""
import random, statistics as st
from fe.intake_report import LAB, MODELS, scored, mae, days, day_stats, B

S = 3


def boot_groups(its, seed):
    rng = random.Random(seed)
    g = {}
    for i in its:
        g.setdefault(LAB[i]["participant"], []).append(i)
    pk = sorted(g)
    return [[(i) for p in (rng.choice(pk) for _ in pk) for i in g[p]] for _ in range(B)]


def q(v, a):
    v = sorted(v)
    return v[int(a * B)], v[int((1 - a) * B) - 1]


def main():
    its = sorted(LAB)
    known = [i for i in its if LAB[i]["served_kcal"]]
    left = {i for i in known if LAB[i]["kcal"] / LAB[i]["served_kcal"] < 0.9}
    eaten = [i for i in known if i not in left]
    left = sorted(left)
    bs = boot_groups(known, 7)
    E = {m: (scored(s)[0], scored(d)[0]) for m, (s, d, _) in MODELS.items()}

    print(f"## 1. Change in MAE% (both photos − before only), by leftover group (served energy known: {len(known)} meals; "
          f"≥10% left: {len(left)}; <10% left: {len(eaten)})\n")
    print("| Model | All meals Δ [95% CI] | ≥10% left Δ [95% CI] | <10% left Δ [95% CI] | Difference (≥10% − <10%) [95% CI] |")
    print("|---|---|---|---|---|")
    for m, (es, ed) in E.items():
        def d(xs):
            return mae(ed, xs) - mae(es, xs)
        L, M, A, D = [], [], [], []
        for b in bs:
            bl = [i for i in b if i in set(left)]
            be = [i for i in b if i not in set(left)]
            L.append(d(bl)); M.append(d(be)); A.append(d(b)); D.append(d(bl) - d(be))
        f = lambda v, x: f"{x:+.1f} [{q(v, .025)[0]:+.1f}, {q(v, .025)[1]:+.1f}]"
        print(f"| {m} | {f(A, d(known))} | {f(L, d(left))} | {f(M, d(eaten))} | {f(D, d(left) - d(eaten))} |")

    print("\n## 2. Decomposition of the before-only error (meals with served energy known), % of total consumed energy\n")
    print("Before-only error vs consumed = (estimate − served) + (served − consumed). The second term is the true leftover (always ≥ 0).\n")
    print("| Model | Estimate − served | Served − consumed (leftover) | = Before-only bias vs consumed | MAE% vs served | MAE% vs consumed | Meals where the two terms offset* |")
    print("|---|---|---|---|---|---|---|")
    tc = sum(LAB[i]["kcal"] for i in known)
    for m, (es, _) in E.items():
        a = sum(es[i] - LAB[i]["served_kcal"] for i in known) / tc * 100
        b = sum(LAB[i]["served_kcal"] - LAB[i]["kcal"] for i in known) / tc * 100
        mae_s = sum(abs(es[i] - LAB[i]["served_kcal"]) for i in known) / sum(LAB[i]["served_kcal"] for i in known) * 100
        off = [i for i in left if es[i] < LAB[i]["served_kcal"]]
        helped = sum(abs(es[i] - LAB[i]["kcal"]) < abs(es[i] - LAB[i]["served_kcal"]) for i in off)
        print(f"| {m} | {a:+.1f} | {b:+.1f} | {a + b:+.1f} | {mae_s:.1f} | {mae(es, known):.1f} | {helped}/{len(left)} |")
    print("\n*Among meals with ≥10% left: under-estimated the served energy AND the estimate is closer to consumed than to served.")

    print("\n## 3. Between-model heterogeneity: Δ MAE% (both − before) of each model minus Haiku 5.5's, all meals [95% CI]\n")
    print("| Model | Δ model − Δ Haiku |")
    print("|---|---|")
    eh_s, eh_d = E["Haiku 5.5"]
    for m, (es, ed) in E.items():
        if m == "Haiku 5.5":
            continue
        v = [(mae(ed, b) - mae(es, b)) - (mae(eh_d, b) - mae(eh_s, b)) for b in bs]
        x = (mae(ed, known) - mae(es, known)) - (mae(eh_d, known) - mae(eh_s, known))
        print(f"| {m} | {x:+.1f} [{q(v, .025)[0]:+.1f}, {q(v, .025)[1]:+.1f}] |")

    dd = days()
    parts = {}
    for k in dd:
        parts.setdefault(k[0], []).append(k)
    pk = sorted(parts)
    rng = random.Random(11)
    bsd = [[k for p in (rng.choice(pk) for _ in pk) for k in parts[p]] for _ in range(B)]
    print(f"\n## 4. Day-level mean error, 90% CI vs ±10% equivalence margin ({len(dd)} days)\n")
    print("| System | Mean day error % | 90% CI | Within ±10% (CI) |")
    print("|---|---|---|---|")
    for m, (es, ed) in E.items():
        for name, e in (("before only", es), ("both photos", ed)):
            mu = day_stats(e, dd)[0]
            v = [day_stats(e, {n: dd[k] for n, k in enumerate(b)})[0] for b in bsd]
            lo, hi = q(v, .05)
            print(f"| {m}, {name} | {mu:+.1f} | [{lo:+.1f}, {hi:+.1f}] | {'yes' if lo > -10 and hi < 10 else 'no'} |")


if __name__ == "__main__":
    main()
