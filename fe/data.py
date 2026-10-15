"""Build the Nutrition5k evaluation splits.

Design (see README):
- Only dishes with an overhead RGB image (the official depth splits).
- Plate grouping: Nutrition5k scans one plate many times as items are added.
  Dishes from the same cafe within 15 minutes where every item of one scan appears
  in the other at the same weight (+-1 g) are the same physical plate.
- search / select: split of official depth_train, grouped by plate (70/30).
- test: official depth_test minus every dish whose plate group also has a
  train dish (cross-split re-scans). Sealed: only `evaluate --final` reads it.
- cafe2: the 238 cafe2 dishes in no official split; dish totals are zero in
  the metadata, so they are recomputed from ingredient rows. Sealed holdout.
- Label hygiene: drop kcal < 30, mass >= 7900 g (scale saturation),
  density > 9.5 kcal/g (above pure fat), any 'deprecated' or 'plate only' row.

Images are copied to data/images/<random id>.png so file names carry no
dish id. Labels live in data/labels/<split>.json, outside what candidates see.
"""
import csv, json, os, random, secrets, shutil, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
GCS = "https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset"
SEED = 20261015


def fetch(rel, dst):
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        urllib.request.urlretrieve(f"{GCS}/{rel}", dst)
    return dst


def load_meta():
    meta = {}
    for cafe in ["cafe1", "cafe2"]:
        p = fetch(f"metadata/dish_metadata_{cafe}.csv", os.path.join(RAW, f"dish_metadata_{cafe}.csv"))
        for r in csv.reader(open(p)):
            ingr = [(r[i + 1].strip(), float(r[i + 2]), float(r[i + 3]), float(r[i + 5]))  # name, grams, kcal, protein... (carb col skipped)
                    for i in range(6, len(r) - 6, 7)]
            kcal, mass = float(r[1]), float(r[2])
            if cafe == "cafe2" and kcal == 0:
                kcal = sum(x[2] for x in ingr)
                mass = mass or sum(x[1] for x in ingr)
            meta[r[0]] = dict(cafe=cafe, kcal=kcal, mass=mass, ingr=ingr)
    return meta


def ids(name):
    p = fetch(f"dish_ids/splits/{name}.txt", os.path.join(RAW, f"{name}.txt"))
    return [l.strip() for l in open(p) if l.strip()]


def clean(m):
    names = [x[0].lower() for x in m["ingr"]]
    return (m["kcal"] >= 30 and m["mass"] > 0 and m["mass"] < 7900
            and m["kcal"] / m["mass"] <= 9.5
            and not any("deprecated" in n or n == "plate only" for n in names))


def plate_groups(dish_ids, meta):
    """Union-find over (cafe, |dt| <= 900 s, one scan's items all present in the other at the same weight)."""
    parent = {d: d for d in dish_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    ts = lambda d: int(d.split("_")[1])
    order = sorted(dish_ids, key=ts)
    grams = {d: {x[0]: x[1] for x in meta[d]["ingr"]} for d in dish_ids}
    for i, a in enumerate(order):
        ga = grams[a]
        for b in order[i + 1:]:
            if ts(b) - ts(a) > 900:
                break
            if meta[a]["cafe"] != meta[b]["cafe"]:
                continue
            gb = grams[b]
            small, big = (ga, gb) if len(ga) <= len(gb) else (gb, ga)
            # incremental re-scan: every item already on the plate keeps its weight
            if small and all(n in big and abs(big[n] - g) <= 1.0 for n, g in small.items()):
                parent[find(a)] = find(b)
    return {d: find(d) for d in dish_ids}


def image_ok(d):
    dst = os.path.join(RAW, "img", f"{d}.png")
    if os.path.exists(dst):
        return True
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    r = subprocess.run(["curl", "-sf", "-o", dst, f"{GCS}/imagery/realsense_overhead/{d}/rgb.png"])
    return r.returncode == 0


def main():
    meta = load_meta()
    train, test = ids("depth_train_ids"), ids("depth_test_ids")
    split_ids = set(train) | set(test)
    cafe2 = [d for d, m in meta.items() if m["cafe"] == "cafe2" and d not in split_ids]

    universe = [d for d in set(train) | set(test) | set(cafe2) if d in meta]
    with ThreadPoolExecutor(24) as ex:
        have = dict(zip(universe, ex.map(image_ok, universe)))
    universe = [d for d in universe if have[d]]

    group = plate_groups(universe, meta)
    train_groups = {group[d] for d in train if d in group}
    report = {}

    clean_test = []
    leaked = 0
    for d in test:
        if d not in group:
            continue
        if group[d] in train_groups:
            leaked += 1
            continue
        clean_test.append(d)
    report["test_dropped_cross_split_rescans"] = leaked

    tr = [d for d in train if d in group]
    groups = sorted({group[d] for d in tr})
    random.Random(SEED).shuffle(groups)
    sel_groups = set(groups[: int(len(groups) * 0.3)])
    splits = {
        "search": [d for d in tr if group[d] not in sel_groups],
        "select": [d for d in tr if group[d] in sel_groups],
        "test": clean_test,
        "cafe2": [d for d in cafe2 if d in group],
    }
    for k in list(splits):
        before = len(splits[k])
        splits[k] = sorted(d for d in splits[k] if clean(meta[d]))
        report[f"{k}_n"] = len(splits[k])
        report[f"{k}_dropped_bad_labels"] = before - len(splits[k])

    img_dir, lab_dir = os.path.join(DATA, "images"), os.path.join(DATA, "labels")
    shutil.rmtree(img_dir, ignore_errors=True)
    os.makedirs(img_dir)
    os.makedirs(lab_dir, exist_ok=True)
    rng = random.Random(SEED)
    for k, ds in splits.items():
        labels = []
        for d in ds:
            anon = "%012x" % rng.getrandbits(48)
            shutil.copyfile(os.path.join(RAW, "img", f"{d}.png"), os.path.join(img_dir, f"{anon}.png"))
            m = meta[d]
            labels.append(dict(item=anon, dish_id=d, plate=group[d], kcal=round(m["kcal"], 2),
                               mass_g=round(m["mass"], 2), ingredients=[[n, round(g, 1)] for n, g, *_ in m["ingr"]]))
        json.dump(labels, open(os.path.join(lab_dir, f"{k}.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(DATA, "split_report.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
