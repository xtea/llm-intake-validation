"""Addendum H analysis (pre-registered Q1–Q3 + secondary macros). Offline. python3 -m fe.intake_report > results/intake.txt"""
import json, os, random, statistics as st
from fe.llm import ROOT

B = 2000
KJ800 = 800 / 4.184
MODELS = {  # name: (single-image run, dual run, subtraction run)
    "Haiku 5.5": ("h0_direct", "dual_direct_haiku", "sub_direct_haiku"),
    "Sonnet 5.5": ("b0_direct", "dual_direct_sonnet", "sub_direct_sonnet"),
    "Opus 5.5": ("b0_direct_opus", "dual_direct_opus", "sub_direct_opus"),
    "GPT-6 luna": ("b0_direct_gpt_6_luna", "dual_direct_gpt_6_luna", "sub_direct_gpt_6_luna"),
    "GPT-6.1 sol": ("b0_direct_gpt_6_1_sol", "dual_direct_gpt_6_1_sol", "sub_direct_gpt_6_1_sol"),
    "GPT-6 astra": ("b0_direct_gpt_6_astra", "dual_direct_gpt_6_astra", "sub_direct_gpt_6_astra"),
    # addendum J (Google), listed only once their runs exist so the earlier tables can still be rebuilt from a checkout without them
    "Gemini 3.8 Flash": ("b0_direct_gemini_flash", "dual_direct_gemini_flash", "sub_direct_gemini_flash"),
    "Gemini 4 Argon": ("b0_direct_gemini_pro", "dual_direct_gemini_pro", "sub_direct_gemini_pro"),
}
MODELS = {m: r for m, r in MODELS.items() if os.path.exists(os.path.join(ROOT, "runs", r[1], "intake-all.json"))}
# Whitton et al. 2024 Table 3 (consumed, day level): estimated as % of true, mean (SD); LoA = mean ± 1.96 SD
RECALL = {"ASA24": (5.4, 29), "Intake24": (1.7, 29), "mFR-TA": (1.3, 15), "IA-24HR": (15.0, 20)}

LAB = {l["item"]: l for l in json.load(open(os.path.join(ROOT, "data", "labels", "acetada_intake.json")))}


def rows(run):
    tag = "acetada_intake-all" if not run.startswith(("dual_", "sub_")) else "intake-all"
    return json.load(open(os.path.join(ROOT, "runs", run, tag + ".json")))["rows"]


def scored(run):
    """est per item; failures scored as the system's worst relative error (evaluator rule, fixed in advance)."""
    rr = [r for r in rows(run) if r["item"] in LAB]
    ok = [r for r in rr if r.get("est") is not None and r["est"] >= 0]
    worst = max(abs(r["est"] - LAB[r["item"]]["kcal"]) / LAB[r["item"]]["kcal"] for r in ok)
    est = {r["item"]: r["est"] for r in ok}
    for r in rr:
        if r["item"] not in est:
            est[r["item"]] = LAB[r["item"]]["kcal"] * (1 + worst)
    return est, {r["item"]: r for r in ok}, len(rr) - len(ok)


def mae(est, its, key="kcal"):
    return sum(abs(est[i] - LAB[i][key]) for i in its) / sum(LAB[i][key] for i in its) * 100


def bias(est, its, key="kcal"):
    return (sum(est[i] for i in its) - sum(LAB[i][key] for i in its)) / sum(LAB[i][key] for i in its) * 100


def boots(its, seed=0):
    rng = random.Random(seed)
    g = {}
    for i in its:
        g.setdefault(LAB[i]["participant"], []).append(i)
    pk = sorted(g)
    return [[i for p in (rng.choice(pk) for _ in pk) for i in g[p]] for _ in range(B)]


def ci(v):
    v = sorted(v)
    return v[int(.025 * B)], v[int(.975 * B)]


def days():
    d = {}
    for i, l in LAB.items():
        d.setdefault((l["participant"], l["date"]), []).append(i)
    return {k: v for k, v in d.items() if sorted(LAB[i]["meal"] for i in v) == ["Breakfast", "Dinner", "Lunch"]}


def day_stats(est, dd, key="kcal"):
    pe, ae = [], []
    for its in dd.values():
        t = sum(LAB[i][key] for i in its)
        e = sum(est[i] for i in its)
        pe.append((e - t) / t * 100)
        ae.append(abs(e - t))
    mu, sd = st.mean(pe), st.stdev(pe)
    return mu, mu - 1.96 * sd, mu + 1.96 * sd, 100 * sum(a <= KJ800 for a in ae) / len(ae)


def main():
    its = sorted(LAB)
    bs = boots(its)
    left = [i for i in its if LAB[i]["served_kcal"] and LAB[i]["kcal"] / LAB[i]["served_kcal"] < 0.9]
    bl = boots(left, 1)
    print(f"ACETADA consumed intake: {len(its)} meals, {len({LAB[i]['participant'] for i in its})} participants; "
          f">=10% energy left: {len(left)} meals\n")
    print("## Q1/Q2 meal level (MAE% of mean consumed energy; bias = total estimate vs total truth)\n")
    print("| Model | Before only: MAE / bias | Subtraction: MAE / bias | Both photos: MAE / bias | Both − before, MAE pts [95% CI] | "
          "Leftover ≥10%: before / both [Δ CI] | fails (s/sub/dual) |")
    print("|---|---|---|---|---|---|---|")
    est_all = {}
    for m, (s, d, sub) in MODELS.items():
        es, _, fs = scored(s)
        ed, rd, fd = scored(d)
        eb, _, fb = scored(sub)
        est_all[m] = (es, ed, eb, rd)
        dl, dh = ci(mae(ed, b) - mae(es, b) for b in bs)
        ll, lh = ci(mae(ed, b) - mae(es, b) for b in bl)
        print(f"| {m} | {mae(es, its):.1f} / {bias(es, its):+.1f} | {mae(eb, its):.1f} / {bias(eb, its):+.1f} | "
              f"{mae(ed, its):.1f} / {bias(ed, its):+.1f} | {mae(ed, its) - mae(es, its):+.1f} [{dl:+.1f}, {dh:+.1f}] | "
              f"{mae(es, left):.1f} / {mae(ed, left):.1f} [{ll:+.1f}, {lh:+.1f}] | {fs}/{fb}/{fd} |")

    print("\n### Eaten fraction read from the photos (both-photos prompt)\n")
    print("| Model | predicted eaten/served median | true median | Spearman |")
    print("|---|---|---|---|")
    for m, (_, _, _, rd) in est_all.items():
        pr = [(r["est"] / r["served_kcal"], LAB[i]["kcal"] / LAB[i]["served_kcal"]) for i, r in rd.items()
              if r.get("served_kcal") and LAB[i]["served_kcal"]]
        print(f"| {m} | {st.median(p for p, _ in pr):.2f} | {st.median(q for _, q in pr):.2f} | {spearman([p for p, _ in pr], [q for _, q in pr]):.2f} |")

    dd = days()
    print(f"\n## Q3 day level: {len(dd)} complete feeding days, {len({k[0] for k in dd})} participants "
          "(thresholds: |mean| ≤ 10%, LoA within ±30%)\n")
    print("| System | Mean day error % [95% CI] | 95% LoA % | Days within 800 kJ % | Meets bias | Meets LoA |")
    print("|---|---|---|---|---|---|")
    parts = {}
    for k in dd:
        parts.setdefault(k[0], []).append(k)
    pk = sorted(parts)
    rng = random.Random(2)
    bsd = [[k for p in (rng.choice(pk) for _ in pk) for k in parts[p]] for _ in range(B)]
    for m, (es, ed, eb, _) in est_all.items():
        for name, e in (("before only", es), ("subtraction", eb), ("both photos", ed)):
            mu, lo, hi, w = day_stats(e, dd)
            vals = sorted(day_stats(e, {n: dd[k] for n, k in enumerate(b)})[0] for b in bsd)
            print(f"| {m}, {name} | {mu:+.1f} [{vals[int(.025 * B)]:+.1f}, {vals[int(.975 * B)]:+.1f}] | {lo:+.0f} to {hi:+.0f} | {w:.0f} | "
                  f"{'yes' if abs(mu) <= 10 else 'no'} | {'yes' if lo >= -30 and hi <= 30 else 'no'} |")
    for k, (mu, sd) in RECALL.items():
        print(f"| *24-h recall {k} (Whitton 2024, n≈143–150 days)* | *{mu:+.1f}* | *{mu - 1.96 * sd:+.0f} to {mu + 1.96 * sd:+.0f}* | — | — | — |")

    print("\n## Secondary: macronutrients eaten, both photos (day level: mean % error, 95% LoA)\n")
    print("| Model | Protein | Carbohydrate | Fat |")
    print("|---|---|---|---|")
    for m, (_, _, _, rd) in est_all.items():
        cells = []
        for key in ("protein_g", "carbs_g", "fat_g"):
            e = {i: r.get(key) for i, r in rd.items() if r.get(key) is not None}
            sub = {k: v for k, v in dd.items() if all(i in e for i in v)}
            mu, lo, hi, _ = day_stats(e, sub, key)
            cells.append(f"{mu:+.0f} ({lo:+.0f} to {hi:+.0f}), n={len(sub)}")
        print(f"| {m} | " + " | ".join(cells) + " |")


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda j: v[j])
        r = [0] * len(v)
        for k, j in enumerate(o):
            r[j] = k
        return r
    a, b = rk(x), rk(y)
    ma, mb = st.mean(a), st.mean(b)
    return sum((p - ma) * (q - mb) for p, q in zip(a, b)) / (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** .5


if __name__ == "__main__":
    main()
