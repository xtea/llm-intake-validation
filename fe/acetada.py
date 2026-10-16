"""Build split `acetada` (FINAL-PLAN addendum E)."""
import csv, json, os, random, subprocess, statistics as st
from fe.data import DATA
R = os.path.join(DATA, "acetada", "ACETADA-release")

def main():
    rows = list(csv.DictReader(open(os.path.join(R, "ACETADA-HF-dataset.csv"))))
    rng = random.Random("acetada")
    labels, skip_density, skip_low, skip_img = [], 0, 0, 0
    for r in rows:
        n = int(r["food_item_count"] or 0)
        served, mass, ingr, bad = 0.0, 0.0, [], False
        for i in range(1, n + 1):
            bef = float(r[f"food_item_{i}_before_portion_g"] or 0)
            con = float(r[f"food_item_{i}_consumed_g"] or 0)
            kc = float(r[f"food_item_{i}_energy_kcal"] or 0)
            if bef <= 0:
                continue
            if con <= 0:
                bad = True
                break
            served += kc / con * bef
            mass += bef
            ingr.append([r[f"food_item_{i}_name"], round(bef, 1)])
        if bad:
            skip_density += 1
            continue
        if served < 30:
            skip_low += 1
            continue
        src = os.path.join(R, r["before_filepath"])
        if not os.path.exists(src):
            skip_img += 1
            continue
        anon = "%012x" % rng.getrandbits(48)
        subprocess.run(["sips", "-s", "format", "png", "-Z", "1024", src, "--out", os.path.join(DATA, "images", anon + ".png")],
                       capture_output=True, check=True)
        labels.append(dict(item=anon, dish_id=r["before_filepath"], plate=r["participant_id"], kcal=round(served, 2),
                           mass_g=round(mass, 1), ingredients=ingr))
    json.dump(labels, open(os.path.join(DATA, "labels", "acetada.json"), "w"), indent=1)
    k = sorted(l["kcal"] for l in labels)
    print(f"meals {len(rows)} kept {len(labels)} skip_density {skip_density} skip_<30 {skip_low} skip_noimg {skip_img} "
          f"participants {len(set(l['plate'] for l in labels))} kcal median {st.median(k):.0f} mass median {st.median(l['mass_g'] for l in labels):.0f}")

if __name__ == "__main__":
    main()
