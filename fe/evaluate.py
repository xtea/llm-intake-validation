"""Score a candidate pipeline on a split.

A candidate is a Python file defining `estimate(image: bytes, llm) -> dict`
returning at least {"kcal": float}; optionally {"mass_g": float}. It gets the
image bytes only (no file name, no dish id) and the shared LLM client.

Anti-gaming: candidate source is checked before running. Only a small set of
stdlib imports is allowed and file/OS/introspection builtins are forbidden,
so a candidate cannot read labels, cached answers or other files. Source size
and literal size are capped so a candidate cannot embed a per-image answer table.

Usage:
  python3 -m fe.evaluate candidates/b0_direct.py --split search --n 60
  python3 -m fe.evaluate candidates/x.py --split select
  python3 -m fe.evaluate candidates/x.py --split test --final   # sealed; logged
"""
import argparse, ast, importlib.util, json, math, os, random, statistics as st, sys, time
from concurrent.futures import ThreadPoolExecutor

from fe.llm import LLM, Budget, ROOT

ALLOWED_IMPORTS = {"json", "re", "math", "statistics", "itertools", "functools", "collections", "fractions"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars",
                   "getattr", "setattr", "delattr", "input", "breakpoint", "memoryview"}
SEALED = {"test", "cafe2", "nvreal"}


MAX_SOURCE_CHARS = 30000
MAX_LITERAL_ITEMS = 40


def check_source(path):
    src = open(path).read()
    if len(src) > MAX_SOURCE_CHARS:
        raise SystemExit(f"{path}: source longer than {MAX_SOURCE_CHARS} chars")
    tree = ast.parse(src, path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    raise SystemExit(f"{path}: import {a.name} not allowed")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                raise SystemExit(f"{path}: from {node.module} not allowed")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise SystemExit(f"{path}: name {node.id} not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise SystemExit(f"{path}: dunder attribute {node.attr} not allowed")
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)) and len(node.elts) > MAX_LITERAL_ITEMS:
            raise SystemExit(f"{path}: literal with more than {MAX_LITERAL_ITEMS} items (no lookup tables)")
        elif isinstance(node, ast.Dict) and len(node.keys) > MAX_LITERAL_ITEMS:
            raise SystemExit(f"{path}: dict literal with more than {MAX_LITERAL_ITEMS} items (no lookup tables)")


def load_candidate(path):
    check_source(path)
    spec = importlib.util.spec_from_file_location("candidate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.estimate


def metrics(rows):
    ok = [r for r in rows if r.get("est") is not None and r["est"] > 0]
    out = {"n": len(rows), "failed": len(rows) - len(ok)}
    if not ok:
        return out
    truth = [r["kcal"] for r in ok]
    ae = [abs(r["est"] - r["kcal"]) for r in ok]
    ape = [abs(r["est"] - r["kcal"]) / r["kcal"] * 100 for r in ok]
    pe = [(r["est"] - r["kcal"]) / r["kcal"] * 100 for r in ok]
    # failures scored as the worst observed relative error so they never help
    worst = max(ape) if ape else 100.0
    mae_pct = (sum(ae) + sum(worst / 100 * r["kcal"] for r in rows if r not in ok)) / sum(r["kcal"] for r in rows) * 100
    out.update(mae_kcal=round(st.mean(ae), 1), mae_pct_of_mean=round(mae_pct, 2),
               median_ape=round(st.median(ape), 1), within20=round(sum(a <= 20 for a in ape) / len(ape) * 100, 1),
               bias_pct=round(st.mean(pe), 1))
    m = [(r["mass_est"], r["mass_g"]) for r in ok if r.get("mass_est")]
    if len(m) > 10:
        lx = [math.log(t) for _, t in m]; ly = [math.log(e) for e, _ in m]
        mx, my = st.mean(lx), st.mean(ly)
        out["mass_slope"] = round(sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx), 3)
        out["mass_median_ratio"] = round(st.median(e / t for e, t in m), 3)
    s = sorted(ok, key=lambda r: r["kcal"])
    for i, lab in enumerate(["small", "mid", "large"]):
        g = s[i * len(s) // 3:(i + 1) * len(s) // 3]
        if g:
            out[f"{lab}_bias_pct"] = round(st.mean((r["est"] - r["kcal"]) / r["kcal"] * 100 for r in g), 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--split", default="search")
    ap.add_argument("--n", type=int, default=0, help="fixed random subset size (0 = all)")
    ap.add_argument("--fold", type=int, default=None, help="search only: disjoint plate-grouped fold 0/1/2")
    ap.add_argument("--seed", default=None, help="subset seed (default: split name, i.e. the same subset every time)")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--max-usd", type=float, default=None)
    a = ap.parse_args()
    if a.split in SEALED and not a.final:
        sys.exit(f"split '{a.split}' is sealed; pass --final (logged) only for the final report")

    labels = json.load(open(os.path.join(ROOT, "data", "labels", f"{a.split}.json")))
    if a.fold is not None:
        labels = [l for l in labels if l.get("fold") == a.fold]
    excl = os.path.join(ROOT, "data", "exclude_nofood.json")
    if os.path.exists(excl):
        bad = set(json.load(open(excl)))
        labels = [l for l in labels if l["item"] not in bad]
    if a.n:
        labels = random.Random(a.seed or a.split).sample(labels, min(a.n, len(labels)))  # same subset per seed
    estimate = load_candidate(a.candidate)
    llm = LLM(max_usd=a.max_usd)
    img_dir = os.path.join(ROOT, "data", "images")

    def run(lab):
        img = open(os.path.join(img_dir, lab["item"] + ".png"), "rb").read()
        row = {"item": lab["item"], "kcal": lab["kcal"], "mass_g": lab["mass_g"]}
        try:
            r = estimate(img, llm)
            row["est"] = float(r["kcal"])
            if r.get("mass_g"):
                row["mass_est"] = float(r["mass_g"])
        except Budget:
            raise
        except Exception as e:  # a crash counts as a failure, not a skip
            row["error"] = repr(e)[:300]
        return row

    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(run, labels))
    res = metrics(rows)
    res.update(candidate=os.path.relpath(a.candidate, ROOT), split=a.split, subset=a.n or "all",
               usd=round(llm.usd, 4), calls=llm.calls, cache_hits=llm.cached, secs=round(time.time() - t0, 1))
    name = os.path.splitext(os.path.basename(a.candidate))[0]
    out_dir = os.path.join(ROOT, "runs", name)
    os.makedirs(out_dir, exist_ok=True)
    tag = f"{a.split}-{a.n or 'all'}" + (f"-s{a.seed}" if a.seed else "") + (f"-f{a.fold}" if a.fold is not None else "")
    json.dump({"metrics": res, "rows": rows}, open(os.path.join(out_dir, f"{tag}.json"), "w"), indent=1)
    if a.final:
        with open(os.path.join(ROOT, "runs", "FINAL-LOG.jsonl"), "a") as f:
            f.write(json.dumps(res) + "\n")
    print(json.dumps(res))


if __name__ == "__main__":
    main()
