"""Addendum D: target-domain recalibration with k labelled dishes (offline). python3 -m fe.recal nvreal"""
import json, math, os, random, sys, statistics as st
from fe.llm import ROOT
from fe.ablation import MODELS, rows, invert

REF = 300


def fit(rs):
    def loss(C, W):
        return sum(abs(REF * math.exp(C + W * math.log(e / REF)) - y) for e, y in rs)
    _, C, W = min((loss(c / 100, w / 100), c / 100, w / 100) for c in range(-80, 81, 2) for w in range(40, 141, 2))
    return C, W


def main():
    split = sys.argv[1] if len(sys.argv) > 1 else "nvreal"
    lab = {l["item"]: l["kcal"] for l in json.load(open(os.path.join(ROOT, "data", "labels", f"{split}.json")))}
    rng = random.Random(1)
    for model, (b0, b2, a, (ca, wa)) in MODELS.items():
        sysd = {}
        for k, r in (("b0", b0), ("b2", b2)):
            x = rows(r, f"{split}-all")
            if x:
                sysd[k] = {i: v["est"] for i, v in x.items()}
        ar = rows(a, f"{split}-all")
        if ar:
            sysd["A-raw"] = {i: invert(ca, wa, v["est"]) for i, v in ar.items()}
        if not sysd:
            continue
        common = sorted(set.intersection(*[set(v) for v in sysd.values()]))
        out = [f"{model:12s}"]
        for name, est in sysd.items():
            base = sum(abs(est[i] - lab[i]) for i in common) / sum(lab[i] for i in common) * 100
            cell = [f"{name}: none {base:.1f}"]
            for k in (10, 20, 50):
                res = []
                for _ in range(200):
                    cal = rng.sample(common, k)
                    rest = [i for i in common if i not in set(cal)]
                    C, W = fit([(est[i], lab[i]) for i in cal])
                    res.append(sum(abs(REF * math.exp(C + W * math.log(est[i] / REF)) - lab[i]) for i in rest) / sum(lab[i] for i in rest) * 100)
                res.sort()
                cell.append(f"k{k} {st.mean(res):.1f} [{res[10]:.1f},{res[189]:.1f}]")
            out.append(" ".join(cell))
        print("  |  ".join(out))


if __name__ == "__main__":
    main()
