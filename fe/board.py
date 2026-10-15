"""Leaderboard: python3 -m fe.board [split-tag]   (default search-300)"""
import glob, json, os, sys
from fe.llm import ROOT

tag = sys.argv[1] if len(sys.argv) > 1 else "search-300"
rows = []
for p in glob.glob(os.path.join(ROOT, "runs", "*", f"{tag}.json")):
    m = json.load(open(p))["metrics"]
    rows.append(m)
rows.sort(key=lambda m: m.get("mae_pct_of_mean", 1e9))
print(f"{'candidate':40s} {'MAE%':>6s} {'medAPE':>6s} {'bias':>6s} {'small':>6s} {'large':>6s} {'slope':>6s} {'fail':>4s} {'$':>6s}")
for m in rows:
    print(f"{m['candidate'][11:51]:40s} {m.get('mae_pct_of_mean',0):6.1f} {m.get('median_ape',0):6.1f} {m.get('bias_pct',0):6.1f} "
          f"{m.get('small_bias_pct',0):6.1f} {m.get('large_bias_pct',0):6.1f} {m.get('mass_slope',0):6.2f} {m['failed']:4d} {m['usd']:6.2f}")
