"""Direction B: consumed intake from before + after photos on ACETADA (FINAL-PLAN addendum H).

  python3 -m fe.intake build                      # labels/acetada_intake.json + after images (PNG, <=1024 px, EXIF dropped)
  python3 -m fe.intake run <candidate> <subset>   # subset: pilot | all ; logs runs/<name>/intake-<subset>.json
  python3 -m fe.intake report pilot               # pilot go/no-go numbers

A candidate defines estimate2(before_png, after_png, llm) -> {"kcal", optional "served_kcal", "leftover_kcal",
"protein_g", "carbs_g", "fat_g"}. The single-image comparator is the existing direct prompt on the before photo
("energy of everything on the plate"), i.e. it assumes everything was eaten.
"""
import csv, json, os, random, statistics as st, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from fe.llm import LLM, ROOT
from fe.evaluate import check_source
import importlib.util

DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "acetada", "ACETADA-release")
AFTER = os.path.join(DATA, "images_after")
LABELS = os.path.join(DATA, "labels", "acetada_intake.json")
# the same before/after pair is attached to two meal rows; the dinner rows are the duplicates (audit 2026-10-16)
DUP_ROWS = {("3057", "2021-08-03", "Dinner"), ("3088", "2021-10-19", "Dinner")}


def build():
    rows = list(csv.DictReader(open(os.path.join(RAW, "ACETADA-HF-dataset.csv"))))
    old = {l["dish_id"]: l["item"] for l in json.load(open(os.path.join(DATA, "labels", "acetada.json")))}
    nofood = set(json.load(open(os.path.join(DATA, "exclude_nofood.json"))))
    rng = random.Random("acetada-intake")
    os.makedirs(AFTER, exist_ok=True)
    out, skip = [], {"dup": 0, "lt30": 0, "nofood": 0}
    f = lambda v: float(v) if v else 0.0
    for r in rows:
        if (r["participant_id"], r["date"], r["meal_type"]) in DUP_ROWS:
            skip["dup"] += 1
            continue
        kcal = f(r["total_kcal"])
        if kcal < 30:
            skip["lt30"] += 1
            continue
        item = old.get(r["before_filepath"]) or "%012x" % rng.getrandbits(48)
        if item in nofood:
            skip["nofood"] += 1
            continue
        served, known = 0.0, True
        for i in range(1, int(r["food_item_count"]) + 1):
            c, e, b = (f(r[f"food_item_{i}_{k}"]) for k in ("consumed_g", "energy_kcal", "before_portion_g"))
            if c > 0:
                served += e / c * b
            elif b > 0:
                known = False
        for src, dst in ((r["before_filepath"], os.path.join(DATA, "images", item + ".png")),
                         (r["after_filepath"], os.path.join(AFTER, item + ".png"))):
            if not os.path.exists(dst):
                subprocess.run(["sips", "-s", "format", "png", "-Z", "1024", os.path.join(RAW, src), "--out", dst],
                               capture_output=True, check=True)
        out.append(dict(item=item, participant=r["participant_id"], date=r["date"], meal=r["meal_type"],
                        kcal=round(kcal, 2), protein_g=round(f(r["total_protein_g"]), 2), carbs_g=round(f(r["total_carbs_g"]), 2),
                        fat_g=round(f(r["total_fat_g"]), 2), served_kcal=round(served, 2) if known else None,
                        in_served_split=r["before_filepath"] in old))
    json.dump(out, open(LABELS, "w"), indent=1)
    print(f"rows {len(rows)} kept {len(out)} skipped {skip} participants {len({l['participant'] for l in out})}")


def subset(name, labels):
    if name == "all":
        return labels
    if name == "pilot":  # 100 meals that also have cached single-image runs; fixed seed, drawn before any dual-image call
        pool = sorted((l for l in labels if l["in_served_split"]), key=lambda l: l["item"])
        return random.Random("pilot-B").sample(pool, 100)
    raise SystemExit(f"unknown subset {name}")


def load2(path):
    check_source(path)
    spec = importlib.util.spec_from_file_location("cand", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.estimate2


def run(cand, name, max_usd=30.0, resample=0):
    labels = subset(name, json.load(open(LABELS)))
    est2 = load2(cand)
    llm = LLM(max_usd=max_usd)
    if resample:  # fresh calls with a different sample index (test-retest); cache keys differ
        base_ask = llm.ask
        llm.ask = lambda *x, sample=0, **k: base_ask(*x, sample=sample + 1000 * resample, **k)

    def one(l):
        b = open(os.path.join(DATA, "images", l["item"] + ".png"), "rb").read()
        a = open(os.path.join(AFTER, l["item"] + ".png"), "rb").read()
        row = {"item": l["item"], "kcal": l["kcal"]}
        try:
            r = est2(b, a, llm)
            row.update(est=float(r["kcal"]), **{k: float(r[k]) for k in ("served_kcal", "leftover_kcal", "protein_g", "carbs_g", "fat_g", "mass_g") if r.get(k) is not None})
        except Exception as e:
            row["error"] = repr(e)[:300]
        return row

    with ThreadPoolExecutor(12) as ex:
        rows = list(ex.map(one, labels))
    tag = os.path.splitext(os.path.basename(cand))[0]
    d = os.path.join(ROOT, "runs", tag)
    os.makedirs(d, exist_ok=True)
    m = {"n": len(rows), "failed": sum("est" not in r for r in rows), "usd": round(llm.usd, 4), "calls": llm.calls, "cache_hits": llm.cached}
    json.dump({"metrics": m, "rows": rows}, open(os.path.join(d, f"intake-{name}" + (f"-r{resample}" if resample else "") + ".json"), "w"), indent=1)
    print(tag, name, m)


def report(name):
    labels = {l["item"]: l for l in json.load(open(LABELS))}
    items = [l["item"] for l in subset(name, list(labels.values()))]
    single = {"Haiku 5.5": "h0_direct", "GPT-6.1 sol": "b0_direct_gpt_6_1_sol"}
    dual = {"Haiku 5.5": "dual_direct_haiku", "GPT-6.1 sol": "dual_direct_gpt_6_1_sol"}

    def load(run, tag):
        p = os.path.join(ROOT, "runs", run, tag + ".json")
        return {r["item"]: r for r in json.load(open(p))["rows"] if r.get("est")} if os.path.exists(p) else {}

    def spearman(x, y):
        rk = lambda v: {i: k for k, i in enumerate(sorted(range(len(v)), key=lambda j: v[j]))}
        rx, ry = rk(x), rk(y)
        a, b = [rx[i] for i in range(len(x))], [ry[i] for i in range(len(y))]
        ma, mb = st.mean(a), st.mean(b)
        return sum((p - ma) * (q - mb) for p, q in zip(a, b)) / (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** .5

    left = [i for i in items if labels[i]["served_kcal"] and labels[i]["kcal"] / labels[i]["served_kcal"] < 0.9]
    print(f"pilot n={len(items)}; meals with >=10% energy left: {len(left)}")
    for m in single:
        s, d = load(single[m], "acetada-all"), load(dual[m], f"intake-{name}")
        its = [i for i in items if i in s and i in d]
        t = lambda e, xs: (sum(abs(e[i]["est"] - labels[i]["kcal"]) for i in xs) / sum(labels[i]["kcal"] for i in xs) * 100,
                           (sum(e[i]["est"] for i in xs) - sum(labels[i]["kcal"] for i in xs)) / sum(labels[i]["kcal"] for i in xs) * 100)
        if not its:
            print(m, "no data")
            continue
        sl = [i for i in its if i in set(left)]
        print(f"{m}: n={len(its)}  single MAE% {t(s, its)[0]:.1f} bias {t(s, its)[1]:+.1f}  |  dual MAE% {t(d, its)[0]:.1f} bias {t(d, its)[1]:+.1f}"
              + (f"  ||  leftover>=10% (n={len(sl)}): single {t(s, sl)[0]:.1f} / dual {t(d, sl)[0]:.1f}" if sl else ""))
        pairs = [(d[i]["est"] / d[i]["served_kcal"], labels[i]["kcal"] / labels[i]["served_kcal"]) for i in its
                 if d[i].get("served_kcal") and labels[i]["served_kcal"]]
        if len(pairs) > 10:
            print(f"   eaten fraction: predicted median {st.median(p for p, _ in pairs):.2f} true median {st.median(q for _, q in pairs):.2f}"
                  f"  Spearman {spearman([p for p, _ in pairs], [q for _, q in pairs]):.2f} (n={len(pairs)})")
        print(f"   failures: dual {len(items) - len([i for i in items if i in d])}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
    elif cmd == "run":
        run(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 30.0, int(sys.argv[5]) if len(sys.argv) > 5 else 0)
    elif cmd == "report":
        report(sys.argv[2])
