"""Final tables with bootstrap CIs (plate-level resampling).

python3 -m fe.report test        # one split
Prints per-candidate MAE% with 95% CI, log-kcal r, log-mass r, bias, $/dish, and paired
differences vs reference candidates (CI of the difference).
"""
import glob, json, math, os, random, sys
from fe.llm import ROOT

B = 2000
REFS = ["h2_plate_scale", "b2_plate_scale", "b2_plate_scale_opus", "compA_v4"]


def load(split):
    out = {}
    for p in glob.glob(os.path.join(ROOT, "runs", "*", f"{split}-all.json")):
        d = json.load(open(p))
        out[os.path.basename(os.path.dirname(p))] = d
    return out


def mae_pct(rows):
    return sum(abs(r["est"] - r["kcal"]) for r in rows) / sum(r["kcal"] for r in rows) * 100


def corr(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))


def main():
    split = sys.argv[1] if len(sys.argv) > 1 else "test"
    runs = load(split)
    labels = {l["item"]: l for l in json.load(open(os.path.join(ROOT, "data", "labels", f"{split}.json")))}
    items = sorted(set.intersection(*[{r["item"] for r in d["rows"]} for d in runs.values()]))
    plates = {}
    for i in items:
        plates.setdefault(labels[i]["plate"], []).append(i)
    pk = sorted(plates)
    R = {n: {r["item"]: r for r in d["rows"]} for n, d in runs.items()}
    worst = {n: max(abs(r["est"] - r["kcal"]) / r["kcal"] for r in d["rows"] if r.get("est")) for n, d in runs.items()}

    def rows_of(n, its):
        out = []
        for i in its:
            r = R[n][i]
            if not r.get("est"):
                r = dict(r, est=r["kcal"] * (1 + worst[n]))  # failure = worst error, never helps
            out.append(r)
        return out

    rng = random.Random(0)
    boots = [[i for p in (rng.choice(pk) for _ in pk) for i in plates[p]] for _ in range(B)]
    res = {}
    for n in runs:
        rr = rows_of(n, items)
        point = mae_pct(rr)
        bs = sorted(mae_pct(rows_of(n, b)) for b in boots)
        rk = corr([math.log(r["est"]) for r in rr], [math.log(r["kcal"]) for r in rr])
        mm = [(math.log(r["mass_est"]), math.log(r["mass_g"])) for r in rr if r.get("mass_est")]
        rm = corr(*zip(*mm)) if len(mm) > 10 else float("nan")
        bias = sum((r["est"] - r["kcal"]) / r["kcal"] for r in rr) / len(rr) * 100   # MPE: mean per-dish percentage error
        mae_k = sum(abs(r["est"] - r["kcal"]) for r in rr) / len(rr)
        m = runs[n]["metrics"]
        res[n] = point
        print(f"{n:28s} MAE% {point:5.1f} [{bs[int(.025*B)]:5.1f},{bs[int(.975*B)]:5.1f}]  r_kcal {rk:.3f}  r_mass {rm:.3f}  "
              f"MPE {bias:+5.1f}  MAEkcal {mae_k:6.1f}  $/dish {m['usd']/max(1,m['n']):.4f}  fail {m['failed']}")
    print(f"\nn = {len(items)} dishes, {len(pk)} plates; paired differences (row − ref), 95% plate-bootstrap CI:")
    for ref in [x for x in REFS if x in runs]:
        for n in runs:
            if n == ref:
                continue
            d = sorted(mae_pct(rows_of(n, b)) - mae_pct(rows_of(ref, b)) for b in boots)
            print(f"  {n:28s} − {ref:22s} {res[n]-res[ref]:+5.1f} [{d[int(.025*B)]:+5.1f},{d[int(.975*B)]:+5.1f}]")


if __name__ == "__main__":
    main()
