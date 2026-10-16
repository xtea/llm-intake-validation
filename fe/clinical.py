"""Clinical anchors (FINAL-PLAN addendum G; exploratory, offline, no model calls).

ACETADA comes from a controlled feeding trial whose main paper (Whitton et al., AJCN 2024) compares four 24-h recall
methods with weighed intake at the level of a participant's feeding day (breakfast + lunch + dinner). We sum our
per-meal estimates the same way and report the same statistics: mean % difference of the day total, Bland-Altman
limits of agreement of the day % error, and the share of days within 800 kJ (191 kcal) of truth. Our label is energy
served, theirs energy consumed (Section 3.2), so the comparison is indicative.

Also: meal-level Bland-Altman and errors by meal and by energy tertile on ACETADA and the Nutrition5k test split.

python3 -m fe.clinical > results/clinical.txt
"""
import json, math, os, random, statistics as st
from fe.llm import ROOT
from fe.ablation import MODELS, rows, fit, apply, invert

KJ800 = 800 / 4.184
B = 2000


def labels(split):
    bad = set(json.load(open(os.path.join(ROOT, "data", "exclude_nofood.json"))))
    return {l["item"]: l for l in json.load(open(os.path.join(ROOT, "data", "labels", f"{split}.json"))) if l["item"] not in bad}


def scored(run, split):
    """est per item; failures scored as the system's own worst relative error (evaluator rule)."""
    p = os.path.join(ROOT, "runs", run, f"{split}-all.json")
    if not os.path.exists(p):
        return None
    rr = json.load(open(p))["rows"]
    ok = [r for r in rr if r.get("est") and r["kcal"] > 0]
    worst = max(abs(r["est"] - r["kcal"]) / r["kcal"] for r in ok)
    return {r["item"]: (r["est"] if r.get("est") else r["kcal"] * (1 + worst)) for r in rr}


def systems(split):
    out = {}
    for model, (b0, b2, a, (ca, wa)) in MODELS.items():
        for name, run in (("Direct", b0), ("Plate", b2)):
            e = scored(run, split)
            if e:
                out[(model, name)] = e
                f0 = rows(run, "search-300-f0")
                if f0 and name == "Direct":
                    C, W = fit(list(f0.values()))
                    out[(model, "Direct + cal")] = {i: apply(C, W, x) for i, x in e.items()}
        e = scored(a, split)
        if e:
            out[(model, "A without cal")] = {i: invert(ca, wa, x) for i, x in e.items()}
            out[(model, "Harness A")] = e
    return out


def meal_slot(dish_id):
    h = int(dish_id.split("_")[-1][:2])
    return "breakfast" if h < 10 else ("lunch" if h < 15 else "dinner")


def days(lab):
    """complete feeding days (3 meals) -> list of items, keyed by (participant, date)."""
    d = {}
    for i, l in lab.items():
        d.setdefault((l["plate"], l["dish_id"].split("/")[2][:10]), []).append(i)
    return {k: v for k, v in d.items() if len(v) == 3 and {meal_slot(lab[i]["dish_id"]) for i in v} == {"breakfast", "lunch", "dinner"}}


def day_stats(est, lab, dd):
    pe, ae = [], []
    for its in dd.values():
        t = sum(lab[i]["kcal"] for i in its)
        e = sum(est[i] for i in its)
        pe.append((e - t) / t * 100)
        ae.append(abs(e - t))
    tot_t = sum(lab[i]["kcal"] for its in dd.values() for i in its)
    tot_e = sum(est[i] for its in dd.values() for i in its)
    sd = st.stdev(pe)
    return {"group_diff": (tot_e - tot_t) / tot_t * 100, "mean_pe": st.mean(pe), "loa": (st.mean(pe) - 1.96 * sd, st.mean(pe) + 1.96 * sd),
            "within800": sum(a <= KJ800 for a in ae) / len(ae) * 100, "mae_pct": sum(ae) / tot_t * 100}


def ci_days(est, lab, dd, key, seed=0):
    rng = random.Random(seed)
    parts = {}
    for k in dd:
        parts.setdefault(k[0], []).append(k)
    pk = sorted(parts)
    vals = []
    for _ in range(B):
        sample = {}
        for n, p in enumerate(rng.choice(pk) for _ in pk):
            for k in parts[p]:
                sample[(n, k)] = dd[k]
        vals.append(day_stats(est, lab, sample)[key])
    vals.sort()
    return vals[int(.025 * B)], vals[int(.975 * B)]


def local_recal(est, lab, dd, k=20, draws=200, seed=1):
    """refit the 2-constant law on k meals from held-out participants; score days of the other participants."""
    rng = random.Random(seed)
    parts = sorted({p for p, _ in dd})
    meals_by_p = {}
    for i, l in lab.items():
        meals_by_p.setdefault(l["plate"], []).append(i)
    res = []
    for _ in range(draws):
        pool = [i for p in parts for i in meals_by_p.get(p, []) if i in est]
        cal = rng.sample(pool, k)
        held = {lab[i]["plate"] for i in cal}
        rs = [{"est": est[i], "kcal": lab[i]["kcal"]} for i in cal]
        C, W = fit(rs)
        e2 = {i: apply(C, W, x) for i, x in est.items()}
        sub = {kk: v for kk, v in dd.items() if kk[0] not in held}
        res.append(day_stats(e2, lab, sub))
    return {key: st.mean(r[key] for r in res) for key in ("mean_pe", "group_diff", "mae_pct", "within800")} | {
        "loa": (st.mean(r["loa"][0] for r in res), st.mean(r["loa"][1] for r in res))}


def meal_ba(est, lab, its):
    pe = [(est[i] - lab[i]["kcal"]) / lab[i]["kcal"] * 100 for i in its]
    m, sd = st.mean(pe), st.stdev(pe)
    return m, m - 1.96 * sd, m + 1.96 * sd


def mae(est, lab, its):
    return sum(abs(est[i] - lab[i]["kcal"]) for i in its) / sum(lab[i]["kcal"] for i in its) * 100


def mpe_total(est, lab, its):
    return (sum(est[i] for i in its) - sum(lab[i]["kcal"] for i in its)) / sum(lab[i]["kcal"] for i in its) * 100


def main():
    lab = labels("acetada")
    dd = days(lab)
    sy = systems("acetada")
    n_days, n_part = len(dd), len({p for p, _ in dd})
    print(f"## ACETADA feeding days (complete: breakfast+lunch+dinner): {n_days} days, {n_part} participants")
    print("Reference (Whitton et al. 2024, same trial, consumed energy, day level): mean % difference "
          "ASA24 5.4, Intake24 1.7, mFR-TA 1.3, IA-24HR 15.0; LoA ~±50% (ASA24, Intake24), within ±30% (mFR-TA), "
          "IA-24HR -25.6..52.5 (carb/protein figure; energy LoA in their Fig 2); within 800 kJ: mFR-TA 45%, others 29-34%.\n")
    print("| Model | System | Mean day error % [95% CI] | Day total diff % | Day MAE % | Day LoA % | Days within 800 kJ % |")
    print("|---|---|---|---|---|---|---|")
    for (model, name), est in sy.items():
        s = day_stats(est, lab, dd)
        lo, hi = ci_days(est, lab, dd, "mean_pe")
        print(f"| {model} | {name} | {s['mean_pe']:+.1f} [{lo:+.1f}, {hi:+.1f}] | {s['group_diff']:+.1f} | {s['mae_pct']:.1f} | "
              f"{s['loa'][0]:+.0f} to {s['loa'][1]:+.0f} | {s['within800']:.0f} |")
    print("\n### Local recalibration on k=20 meals from other participants (mean of 200 draws)\n")
    print("| Model | System | Mean day error % | Day total diff % | Day MAE % | Day LoA % | Days within 800 kJ % |")
    print("|---|---|---|---|---|---|---|")
    for (model, name), est in sy.items():
        if name in ("Direct", "Plate", "A without cal"):
            s = local_recal(est, lab, dd)
            print(f"| {model} | {name} + local cal (k=20) | {s['mean_pe']:+.1f} | {s['group_diff']:+.1f} | {s['mae_pct']:.1f} | "
                  f"{s['loa'][0]:+.0f} to {s['loa'][1]:+.0f} | {s['within800']:.0f} |")

    for split in ("acetada", "test"):
        lab = labels(split)
        sy = systems(split)
        its_all = list(lab)
        ks = sorted(its_all, key=lambda i: lab[i]["kcal"])
        terc = {"low": ks[:len(ks) // 3], "mid": ks[len(ks) // 3:2 * len(ks) // 3], "high": ks[2 * len(ks) // 3:]}
        cut = (lab[terc["mid"][0]]["kcal"], lab[terc["high"][0]]["kcal"])
        strata = dict(terc)
        if split == "acetada":
            for slot in ("breakfast", "lunch", "dinner"):
                strata[slot] = [i for i in its_all if meal_slot(lab[i]["dish_id"]) == slot]
        print(f"\n## {split}: meal level (n={len(its_all)}; energy tertile cut points {cut[0]:.0f} / {cut[1]:.0f} kcal)\n")
        print("| Model | System | Bias % | LoA % | " + " | ".join(f"MAE% {k} (n={len(v)}) / total diff %" for k, v in strata.items()) + " |")
        print("|---|---|---|---|" + "---|" * len(strata))
        for (model, name), est in sy.items():
            its = [i for i in its_all if i in est]
            m, lo, hi = meal_ba(est, lab, its)
            cells = [f"{mae(est, lab, v):.1f} / {mpe_total(est, lab, v):+.0f}" for v in strata.values()]
            print(f"| {model} | {name} | {m:+.1f} | {lo:+.0f} to {hi:+.0f} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
