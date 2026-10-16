"""Build split `n5k_side`: official rgb_test (709, uncleaned), one side-angle frame per dish (camera A, fallback B/C/D).
Downloads only the first ~3 MB of each video and decodes the first frame with ffmpeg."""
import json, os, random, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from fe.data import load_meta, ids, DATA, GCS

def frame(d):
    out = os.path.join(DATA, "raw", "side", f"{d}.png")
    if os.path.exists(out):
        return d, out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for cam in "ABCD":
        with tempfile.TemporaryDirectory() as t:
            v = os.path.join(t, "v.h264")
            r = subprocess.run(["curl", "-sf", "-r", "0-3000000", "-o", v, f"{GCS}/imagery/side_angles/{d}/camera_{cam}.h264"])
            if r.returncode:
                continue
            f = os.path.join(t, "f.png")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", v, "-frames:v", "1", f], capture_output=True)
            if os.path.exists(f):
                subprocess.run(["sips", "-s", "format", "png", "-Z", "1024", f, "--out", out], capture_output=True)
                return d, out
    return d, None

def main():
    meta = load_meta()
    test = [d for d in ids("rgb_test_ids") if d in meta]
    with ThreadPoolExecutor(16) as ex:
        res = dict(ex.map(frame, test))
    rng = random.Random("n5k_side")
    labels = []
    for d in test:
        if not res[d]:
            continue
        anon = "%012x" % rng.getrandbits(48)
        os.replace(res[d], os.path.join(DATA, "images", anon + ".png")) if False else subprocess.run(["cp", res[d], os.path.join(DATA, "images", anon + ".png")])
        m = meta[d]
        labels.append(dict(item=anon, dish_id=d, plate=d, kcal=round(m["kcal"], 2), mass_g=round(m["mass"], 2),
                           ingredients=[[n, round(g, 1)] for n, g, *_ in m["ingr"]]))
    json.dump(labels, open(os.path.join(DATA, "labels", "n5k_side.json"), "w"), indent=1)
    print("rgb_test", len(test), "with frame", len(labels))

if __name__ == "__main__":
    main()
