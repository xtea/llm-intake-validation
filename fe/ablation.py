"""Post-review calibration ablation (FINAL-PLAN addendum B; exploratory).

For each model: fit kcal = 300*exp(C + W*ln(x/300)) on search fold 0 (300 dishes) for the direct prompt (b0) and the
plate-as-ruler prompt (b2); apply unchanged to sealed splits. Harness A without calibration is recovered exactly by inverting
its fitted map (A's final step is the same 2-constant power law on the geometric mean of its views).

python3 -m fe.ablation test|cafe2|nvreal|n5k_side
"""
import json, math, os, random, sys
from fe.llm import ROOT

REF = 300
B = 2000
MODELS = {
    # name: (b0 run, b2 run, harness-A run, (C, W) of harness A)
    "Haiku 5.5": ("h0_direct", "h2_plate_scale", "compA_v4", (-0.0738, 0.9295)),
    "Sonnet 5.5": ("b0_direct", "b2_plate_scale", "compA_v4_sonnet_cal", (-0.04, 0.87)),
    "Opus 5.5": ("b0_direct_opus", "b2_plate_scale_opus", "compA_v4_opus_cal", (-0.12, 0.945)),
    "gpt-6-luna": ("b0_direct_gpt_6_luna", "b2_plate_scale_gpt_6_luna", "compA_v4_cal_gpt_6_luna", (-0.035, 0.855)),
    "gpt-6.1-sol": ("b0_direct_gpt_6_1_sol", "b2_plate_scale_gpt_6_1_sol", "compA_v4_cal_gpt_6_1_sol", (-0.27, 1.02)),
    "gpt-6-astra": ("b0_direct_gpt_6_astra", "b2_plate_scale_gpt_6_astra", "compA_v4_cal_gpt_6_astra", (-0.27, 0.99)),
}


def rows(name, tag):
    p = os.path.join(ROOT, "runs", name, f"{tag}.json")
    if not os.path.exists(p):
        return None
    return {r["item"]: r for r in json.load(open(p))["rows"] if r.get("est")}


def fit(rs):
    def loss(C, W):
        return sum(abs(REF * math.exp(C + W * math.log(r["est"] / REF)) - r["kcal"]) for r in rs)
    _, C, W = min((loss(c / 1000, w / 1000), c / 1000, w / 1000) for c in range(-400, 101, 5) for w in range(500, 1201, 5))
    return C, W


def apply(C, W, x):
    return REF * math.exp(C + W * math.log(x / REF))


def invert(C, W, y):
    return REF * math.exp((math.log(y / REF) - C) / W)


def main():
    split = sys.argv[1] if len(sys.argv) > 1 else "test"
    labels = {l["item"]: l for l in json.load(open(os.path.join(ROOT, "data", "labels", f"{split}.json")))}
    rng = random.Random(0)
    print(f"split={split}  (MAE% of mean; 95% plate-bootstrap CI for difference vs harness A)")
    for model, (b0, b2, a, (ca, wa)) in MODELS.items():
        sys_est = {}
        fold = {}
        for key, run in (("b0", b0), ("b2", b2)):
            f0 = rows(run, "search-300-f0")
            sp = rows(run, f"{split}-all")
            if sp is None:
                continue
            sys_est[key] = {i: r["est"] for i, r in sp.items()}
            if f0:
                C, W = fit(list(f0.values()))
                fold[key] = (C, W)
                sys_est[key + "+cal"] = {i: apply(C, W, r["est"]) for i, r in sp.items()}
        ar = rows(a, f"{split}-all")
        if ar:
            sys_est["A-raw"] = {i: invert(ca, wa, r["est"]) for i, r in ar.items()}
            sys_est["A"] = {i: r["est"] for i, r in ar.items()}
        if not sys_est:
            continue
        common = sorted(set.intersection(*[set(v) for v in sys_est.values()]))
        plates = {}
        for i in common:
            plates.setdefault(labels[i]["plate"], []).append(i)
        pk = sorted(plates)
        boots = [[i for p in (rng.choice(pk) for _ in pk) for i in plates[p]] for _ in range(B)]
        mae = lambda est, its: sum(abs(est[i] - labels[i]["kcal"]) for i in its) / sum(labels[i]["kcal"] for i in its) * 100
        line = [f"{model:12s} n={len(common):3d}"]
        for k in ["b0", "b0+cal", "b2", "b2+cal", "A-raw", "A"]:
            if k not in sys_est:
                line.append(f"{k} --")
                continue
            v = mae(sys_est[k], common)
            if k != "A" and "A" in sys_est:
                d = sorted(mae(sys_est[k], b) - mae(sys_est["A"], b) for b in boots)
                line.append(f"{k} {v:5.1f} (Δ{v - mae(sys_est['A'], common):+.1f} [{d[int(.025*B)]:+.1f},{d[int(.975*B)]:+.1f}])")
            else:
                line.append(f"{k} {v:5.1f}")
        print("  ".join(line))
        if fold:
            print("    fold-0 fits:", {k: tuple(round(x, 3) for x in v) for k, v in fold.items()})


if __name__ == "__main__":
    main()
