"""Paper 4B tables in the manuscript's exact markdown formats, rebuilt from cached model outputs (no API calls).

    python3 -m fe.paper_tables_B > results/paper_tables_B.md

Blocks are separated by lines `<<NAME>>`; doc/credit/drafts/paper4B_fill.py pastes them into the manuscript.
Numbers use the typographic minus (−) and the no-break space inside [lo, hi] as the manuscript does.
Model set = fe.intake_report.MODELS (rows appear in that order).
"""
import csv, json, math, os, random, statistics as st
import numpy as np
from fe.llm import ROOT
from fe.intake_report import LAB, MODELS, scored, mae, bias, days, day_stats, B, KJ800
from fe.intake_rev2 import rm_loa, spearman, ANIMAL
from fe.intake_abl import load as abl_load, scored_rows, KEY
from fe.intake import subset
from fe.ablation import fit, apply

ITS = sorted(LAB)
KNOWN = [i for i in ITS if LAB[i]["served_kcal"]]
LEFT = [i for i in KNOWN if 1 - LAB[i]["kcal"] / LAB[i]["served_kcal"] >= .1]
NOTLEFT = [i for i in KNOWN if i not in set(LEFT)]
DD = days()
NB = " "  # no-break space inside intervals


def m_(s):
    return s.replace("-", "−")


def f1(x):  # unsigned 1 dp
    return m_(f"{x:.1f}")


def s1(x):  # signed 1 dp
    return m_(f"{x:+.1f}")


def s0(x):
    return m_(f"{x:+.0f}")


def ci_(lo, hi, d=1):
    return m_(f"[{lo:+.{d}f},{NB}{hi:+.{d}f}]")


def pboot(its, seed):
    rng = random.Random(seed)
    g = {}
    for i in its:
        g.setdefault(LAB[i]["participant"], []).append(i)
    pk = sorted(g)
    return [[i for p in (rng.choice(pk) for _ in pk) for i in g[p]] for _ in range(B)]


def dboot(seed):
    parts = {}
    for k in DD:
        parts.setdefault(k[0], []).append(k)
    pk = sorted(parts)
    rng = random.Random(seed)
    return [[k for p in (rng.choice(pk) for _ in pk) for k in parts[p]] for _ in range(B)]


def q(v, a):
    v = sorted(v)
    return v[int(a * B)], v[int((1 - a) * B) - 1]


E = {m: tuple(scored(r)[0] for r in runs) for m, runs in MODELS.items()}  # (before, both, subtraction)
OK = {m: tuple(scored(r)[1] for r in runs) for m, runs in MODELS.items()}
NF = {m: tuple(scored(r)[2] for r in runs) for m, runs in MODELS.items()}
# leave-one-participant-out share eaten
_parts = sorted({LAB[i]["participant"] for i in ITS})
_te = {p: sum(LAB[i]["kcal"] for i in KNOWN if LAB[i]["participant"] == p) for p in _parts}
_ts = {p: sum(LAB[i]["served_kcal"] for i in KNOWN if LAB[i]["participant"] == p) for p in _parts}
_TE, _TS = sum(_te.values()), sum(_ts.values())
C = {p: (_TE - _te[p]) / (_TS - _ts[p]) for p in _parts}
EC = {m: {i: E[m][0][i] * C[LAB[i]["participant"]] for i in ITS} for m in MODELS}
BS = pboot(ITS, 32)
BL = pboot(LEFT, 33)
BSD = dboot(11)


def block(name, lines):
    print(f"<<{name}>>")
    print("\n".join(lines))
    print()


def table2():
    L = ["| Model | Before only | Before × c | Subtraction | Both photos | Both photos, valid subset (n) | Δ vs before only | Δ vs before × c | Δ vs before × c, ≥10% left |",
         "|---|---|---|---|---|---|---|---|---|"]
    bs0 = pboot(ITS, 0)
    for m in MODELS:
        es, ed, eb = E[m]
        ok = set(OK[m][0]) & set(OK[m][1]) & set(OK[m][2])
        valid = [i for i in ITS if i in ok]
        d1 = lambda its: mae(ed, its) - mae(es, its)
        d2 = lambda its: mae(ed, its) - mae(EC[m], its)
        L.append(f"| {m} | {f1(mae(es, ITS))} ({s1(bias(es, ITS))}) | {f1(mae(EC[m], ITS))} | {f1(mae(eb, ITS))} ({s1(bias(eb, ITS))}) | "
                 f"{f1(mae(ed, ITS))} ({s1(bias(ed, ITS))}) | {f1(mae(ed, valid))} ({len(valid)}) | "
                 f"{s1(d1(ITS))} {ci_(*q([d1(b) for b in bs0], .025))} | {s1(d2(ITS))} {ci_(*q([d2(b) for b in BS], .025))} | "
                 f"{s1(d2(LEFT))} {ci_(*q([d2(b) for b in BL], .025))} |")
    block("TABLE2", L)


def table3():
    L = ["| Model | (1) Before, simple prompt | (3b) Before, structured prompt | (3a) Both photos, simple prompt | (3) Both photos, structured prompt | Photo effect, structured prompt (3) − (3b) | Photo effect, simple prompt (3a) − (1) | Prompt effect, before only (3b) − (1) | Prompt effect, both photos (3) − (3a) |",
         "|---|---|---|---|---|---|---|---|---|"]
    bs = pboot(ITS, 61)
    day = ["**Day level for the ablation conditions** (mean e_day %; 95% LoA; days within 800 kJ %). (1) / (3b) / (3a) / (3): "]
    parts = []
    for m, (s1_, s3, _) in MODELS.items():
        k = KEY[m]
        r3a = abl_load(f"dual_simple_{k}", "intake-all"); r3b = abl_load(f"before_struct_{k}", "intake-all")
        e1, e3 = E[m][0], E[m][1]
        e3a = scored_rows(r3a)[0]; e3b = scored_rows(r3b)[0]
        d = lambda ea, eb, its: mae(ea, its) - mae(eb, its)
        cells = [f"{f1(mae(e, ITS))} ({s1(bias(e, ITS))})" for e in (e1, e3b, e3a, e3)]
        effs = [f"{s1(d(ea, eb, ITS))} {ci_(*q([d(ea, eb, b) for b in bs], .025))}" for ea, eb in ((e3, e3b), (e3a, e1), (e3b, e1), (e3, e3a))]
        L.append(f"| {m} | " + " | ".join(cells) + " | " + " | ".join(effs) + " |")
        ds = [day_stats(e, DD) for e in (e1, e3b, e3a, e3)]
        parts.append(f"{m} " + " / ".join(f"{s1(mu)}, {s0(lo)}..{s0(hi)}, {w:.0f}" for mu, lo, hi, w in ds))
    block("TABLE3", L)
    block("ABL_DAY_TEXT", [day[0] + ". ".join(parts) + "."])


def table4():
    L = ["| Model | Estimate − served | Energy left | Estimate − eaten | Meals with ≥10% left where the two parts offset* | Median offset, kcal |",
         "|---|---|---|---|---|---|"]
    n = len(KNOWN)
    left_mean = st.mean(LAB[i]["served_kcal"] - LAB[i]["kcal"] for i in KNOWN)
    for m in MODELS:
        es = E[m][0]
        a = st.mean(es[i] - LAB[i]["served_kcal"] for i in KNOWN)
        c = st.mean(es[i] - LAB[i]["kcal"] for i in KNOWN)
        off = [i for i in LEFT if es[i] < LAB[i]["served_kcal"] and abs(es[i] - LAB[i]["kcal"]) < abs(es[i] - LAB[i]["served_kcal"])]
        moved = [min(LAB[i]["served_kcal"] - es[i], LAB[i]["served_kcal"] - LAB[i]["kcal"]) for i in off]
        L.append(f"| {m} | {s0(a)} | {s0(left_mean)} | {s0(c)} | {len(off)} / {len(LEFT)} | {st.median(moved):.0f} |")
    block("TABLE4", L)


def table5():
    L = ["| Model, input | Mean day error % | 90% CI | Equivalence | 95% LoA % | Days within 800 kJ % |", "|---|---|---|---|---|---|"]
    C_rows = ["| Model | Before only | Subtraction | Both photos |", "|---|---|---|---|"]
    for m in MODELS:
        es, ed, eb = E[m]
        cells = []
        for name, e in (("before only", es), ("both photos", ed)):
            mu, lo, hi, w = day_stats(e, DD)
            v = [day_stats(e, {n: DD[k] for n, k in enumerate(b)})[0] for b in BSD]
            l95, h95 = q(v, .025); l90, h90 = q(v, .05)
            eq = "yes" if l90 > -10 and h90 < 10 else "no"
            L.append(f"| {m}, {name} | {s1(mu)} {ci_(l95, h95)} | {s1(l90)}, {s1(h90)} | {eq} | {s0(lo)} to {s0(hi)} | {w:.0f} |")
        for e in (es, eb, ed):
            mu, lo, hi, w = day_stats(e, DD)
            v = [day_stats(e, {n: DD[k] for n, k in enumerate(b)})[0] for b in BSD]
            l95, h95 = q(v, .025)
            cells.append(f"{s1(mu)} {ci_(l95, h95)}; {s0(lo)} to {s0(hi)}; {w:.0f}")
        C_rows.append(f"| {m} | " + " | ".join(cells) + " |")
    block("TABLE5", L)
    block("APPC", C_rows)
    # LoA uncertainty for the both-photos condition (bootstrap of the limits), used in the text
    T = []
    for m in MODELS:
        ed = E[m][1]
        los, his = [], []
        for b in BSD:
            v = [(sum(ed[i] for i in DD[k]) - sum(LAB[i]["kcal"] for i in DD[k])) / sum(LAB[i]["kcal"] for i in DD[k]) * 100 for k in b]
            mu, sd = st.mean(v), st.stdev(v)
            los.append(mu - 1.96 * sd); his.append(mu + 1.96 * sd)
        T.append(f"{m} lower {ci_(*q(los, .025), 0)}, upper {ci_(*q(his, .025), 0)}")
    block("LOA_CI_TEXT", ["Bootstrap 95% CIs of the day-level limits of agreement, both photos: " + "; ".join(T) + "."])


def table7():
    L = ["| Model | Protein | Carbohydrate | Fat |", "|---|---|---|---|"]
    for m in MODELS:
        ok = OK[m][1]
        cells = []
        for key in ("protein_g", "carbs_g", "fat_g"):
            pe = []
            for its in DD.values():
                if all(i in ok and ok[i].get(key) is not None for i in its):
                    t = sum(LAB[i][key] for i in its)
                    pe.append((sum(ok[i][key] for i in its) - t) / t * 100)
            mu, sd = st.mean(pe), st.stdev(pe)
            cells.append(f"{s0(mu)} ({s0(mu - 1.96 * sd)} to {s0(mu + 1.96 * sd)})")
        L.append(f"| {m} | " + " | ".join(cells) + " |")
    block("TABLE7", L)


def appd():
    L = ["| Model | Meal MAE%: none → cal | Day mean %: none → cal | Day 95% LoA: none → cal | Days within 800 kJ %: none → cal |", "|---|---|---|---|---|"]
    rng = random.Random(5)
    for m in MODELS:
        ed = E[m][1]
        res = []
        for _ in range(200):
            cal = rng.sample(ITS, 20)
            held = {LAB[i]["participant"] for i in cal}
            Cc, W = fit([{"est": max(ed[i], 1.0), "kcal": LAB[i]["kcal"]} for i in cal])
            e2 = {i: apply(Cc, W, max(x, 1.0)) for i, x in ed.items()}
            sub = {kk: v for kk, v in DD.items() if kk[0] not in held}
            rest = [i for i in ITS if LAB[i]["participant"] not in held]
            res.append((mae(ed, rest), mae(e2, rest), day_stats(ed, sub), day_stats(e2, sub)))
        f = lambda j: st.mean(r[j] for r in res)
        g = lambda j, t: st.mean(r[j][t] for r in res)
        L.append(f"| {m} | {f1(f(0))} → {f1(f(1))} | {s1(g(2, 0))} → {s1(g(3, 0))} | {s0(g(2, 1))}..{s0(g(2, 2))} → {s0(g(3, 1))}..{s0(g(3, 2))} | {g(2, 3):.0f} → {g(3, 3):.0f} |")
    block("APPD_RECAL", L)
    meals = {k: [i for i in ITS if LAB[i]["meal"] == k] for k in ("Breakfast", "Lunch", "Dinner")}
    L = ["| Model | " + " | ".join(f"{k} (n = {len(v)})" for k, v in meals.items()) + " |", "|---|---|---|---|"]
    for m in MODELS:
        ed = E[m][1]
        L.append(f"| {m} | " + " | ".join(f"{f1(mae(ed, v))} / {s1(bias(ed, v))}" for v in meals.values()) + " |")
    block("APPD_MEAL", L)


def appf():
    L = ["| Model | MAE% before×c / both | Δ both − before×c, all [95% CI] | Δ, ≥10% left [95% CI] | Day mean %: before×c / both | Day LoA %: before×c / both | Days within 800 kJ %: before×c / both |",
         "|---|---|---|---|---|---|---|"]
    for m in MODELS:
        ed, ec = E[m][1], EC[m]
        d = lambda its: mae(ed, its) - mae(ec, its)
        a, b_ = day_stats(ec, DD), day_stats(ed, DD)
        L.append(f"| {m} | {f1(mae(ec, ITS))} / {f1(mae(ed, ITS))} | {s1(d(ITS))} {ci_(*q([d(x) for x in BS], .025))} | {s1(d(LEFT))} {ci_(*q([d(x) for x in BL], .025))} | "
                 f"{s1(a[0])} / {s1(b_[0])} | {s0(a[1])}..{s0(a[2])} / {s0(b_[1])}..{s0(b_[2])} | {a[3]:.0f} / {b_[3]:.0f} |")
    block("APPF_FIXED", L)
    L = ["| Model | ≥10% left | <10% left | Difference |", "|---|---|---|---|"]
    bs = pboot(KNOWN, 41)
    for m in MODELS:
        es, ed = E[m][0], E[m][1]
        dm = lambda its: st.mean(abs(ed[i] - LAB[i]["kcal"]) - abs(es[i] - LAB[i]["kcal"]) for i in its)
        sl = set(LEFT)
        vl, vm, vd = [], [], []
        for b in bs:
            a_, c_ = dm([i for i in b if i in sl]), dm([i for i in b if i not in sl])
            vl.append(a_); vm.append(c_); vd.append(a_ - c_)
        a0, c0 = dm(LEFT), dm(NOTLEFT)
        L.append(f"| {m} | {s0(a0)} {ci_(*q(vl, .025), 0)} | {s0(c0)} {ci_(*q(vm, .025), 0)} | {s0(a0 - c0)} {ci_(*q(vd, .025), 0)} |")
    block("APPF_KCAL", L)
    # without the pilot
    lab_list = json.load(open(os.path.join(ROOT, "data", "labels", "acetada_intake.json")))
    pilot = {l["item"] for l in subset("pilot", lab_list)}
    pilot_p = {LAB[i]["participant"] for i in pilot}
    k1 = [i for i in ITS if i not in pilot]; k2 = [i for i in ITS if LAB[i]["participant"] not in pilot_p]
    d1 = {k: {kk: v for kk, v in DD.items() if all(i in set(k) for i in v)} for k in ()}  # placeholder
    n_days = lambda keep: len({kk for kk, v in DD.items() if all(i in set(keep) for i in v)})
    parts = []
    for m in MODELS:
        es, ed = E[m][0], E[m][1]
        parts.append(f"{m} {s1(mae(ed, k1) - mae(es, k1))} / {s1(mae(ed, k2) - mae(es, k2))}")
    block("APPF_PILOT_TEXT", [f"**Without the pilot.** Excluding the 100 pilot meals leaves {len(k1)} meals and {n_days(k1)} complete days; excluding all pilot participants leaves "
                              f"{len(k2)} meals and {n_days(k2)} complete days. MAE% change (both − before), all meals: " + ", ".join(parts) + "."])
    # pairwise
    names = list(MODELS)
    short = {n: n.replace(" 5.5", "").replace("GPT-6.1 ", "").replace("GPT-6 ", "").replace("Gemini 3.8 ", "").replace("Gemini 4 ", "") for n in names}
    rng = random.Random(51)
    g = {}
    for i in ITS:
        g.setdefault(LAB[i]["participant"], []).append(i)
    pk = sorted(g)
    dl = {m: (lambda its, m=m: mae(E[m][1], its) - mae(E[m][0], its)) for m in names}
    pair = {}
    rng_, sd_ = [], []
    for _ in range(B):
        b = [i for p in (rng.choice(pk) for _ in pk) for i in g[p]]
        db = {m: dl[m](b) for m in names}
        v = list(db.values()); rng_.append(max(v) - min(v)); sd_.append(st.pstdev(v))
        for a in range(len(names)):
            for c in range(a + 1, len(names)):
                pair.setdefault((names[a], names[c]), []).append(db[names[a]] - db[names[c]])
    d0 = {m: dl[m](ITS) for m in names}
    v = list(d0.values())
    txt = "; ".join(f"{short[a]}−{short[c]} {s1(d0[a] - d0[c])} {ci_(*q(vals, .025))}" for (a, c), vals in pair.items())
    npairs = len(pair)
    block("APPF_PAIRS_TEXT", [f"**Between-model differences in Δ MAE% (both − before), all {npairs} pairs, unadjusted [95% CI].** {txt}."])
    block("HETERO_TEXT", [f"range of Δ across models {f1(max(v) - min(v))} points {ci_(*q(rng_, .025))}; SD {f1(st.pstdev(v))} {ci_(*q(sd_, .025))}; {sum(x < 0 for x in v)} of {len(v)} negative"])
    # RM / log
    parts = []
    icc_lo, icc_hi = 9, 0
    for m in MODELS:
        ed = E[m][1]
        by, logs = {}, {}
        for (p, _), its in DD.items():
            t = sum(LAB[i]["kcal"] for i in its); e = sum(ed[i] for i in its)
            by.setdefault(p, []).append((e - t) / t * 100); logs.setdefault(p, []).append(math.log(e / t))
        gm, lo, hi, icc, sw = rm_loa(by); lg = rm_loa(logs)
        icc_lo, icc_hi = min(icc_lo, icc), max(icc_hi, icc)
        parts.append(f"{m} {sw:.1f} / {icc:.2f} / ×{math.exp(lg[1]):.2f}–×{math.exp(lg[2]):.2f}")
    block("APPF_RM_TEXT", ["**Day-level agreement, repeated-measures and log-scale** (both photos). Within-participant SD of e_day / ICC / ratio LoA (estimate ÷ truth): " + "; ".join(parts) + f". ICC range {icc_lo:.2f} to {icc_hi:.2f}."])
    # shrinkage slopes
    parts = []
    for m in MODELS:
        ed = E[m][1]
        x = np.log([LAB[i]["kcal"] for i in ITS]); y = np.log([max(ed[i], 1) for i in ITS]); bm = np.polyfit(x, y, 1)[0]
        xd = np.log([sum(LAB[i]["kcal"] for i in v) for v in DD.values()]); yd = np.log([sum(ed[i] for i in v) for v in DD.values()]); bd = np.polyfit(xd, yd, 1)[0]
        pe = [(math.exp(b) - math.exp(a)) / math.exp(a) * 100 for a, b in zip(xd, yd)]; bp = np.polyfit(xd / math.log(2), pe, 1)[0]
        parts.append(f"{m} meal {bm:.2f}, day {bd:.2f}, {s1(bp)} pts per doubling")
    block("SHRINK_TEXT", ["; ".join(parts)])
    # protein vs composition
    R = list(csv.DictReader(open(os.path.join(ROOT, "data", "acetada", "ACETADA-release", "ACETADA-HF-dataset.csv"))))
    key = {(l["participant"], l["date"], l["meal"]): i for i, l in LAB.items()}
    comp = {}
    fv = lambda v: float(v) if v else 0.0
    for r in R:
        i = key.get((r["participant_id"], r["date"], r["meal_type"]))
        if not i:
            continue
        e_an = e_tot = p_tot = 0.0
        for k in range(1, int(r["food_item_count"]) + 1):
            n = r[f"food_item_{k}_name"].lower(); e = fv(r[f"food_item_{k}_energy_kcal"]); p = fv(r[f"food_item_{k}_protein_g"])
            e_tot += e; p_tot += p
            if any(a in n for a in ANIMAL):
                e_an += e
        if e_tot > 0:
            comp[i] = (e_an / e_tot, p_tot / e_tot * 100)
    parts = []; tot_rng = []; sp_d = []; sp_a = []
    for m in MODELS:
        rd = OK[m][1]
        its = [i for i in comp if i in rd and rd[i].get("protein_g") is not None and LAB[i]["protein_g"] > 0]
        err = [(rd[i]["protein_g"] - LAB[i]["protein_g"]) / LAB[i]["protein_g"] * 100 for i in its]
        bb = lambda xs: (sum(rd[i]["protein_g"] for i in xs) - sum(LAB[i]["protein_g"] for i in xs)) / sum(LAB[i]["protein_g"] for i in xs) * 100
        lo_ = [i for i in its if comp[i][0] < 1 / 3]; hi_ = [i for i in its if comp[i][0] >= 1 / 3]
        sd_ = spearman(err, [comp[i][1] for i in its]); sa_ = spearman(err, [comp[i][0] for i in its])
        sp_d.append(sd_); sp_a.append(sa_); tot_rng.append(bb(its))
        parts.append(f"{m} {m_(f'{sd_:.2f}')}, {m_(f'{sa_:.2f}')}; {s0(bb(lo_))}% vs {s0(bb(hi_))}%")
    block("APPF_PROTEIN_TEXT", ["**Protein error and meal composition** (both photos; Spearman with protein density g/100 kcal, Spearman with animal-source energy share; bias in meals with animal share <1/3 vs ≥1/3): " + ". ".join(parts) + "."])
    block("PROTEIN_RANGES", [f"protein bias {s0(min(tot_rng))}% to {s0(max(tot_rng))}%; Spearman density {m_(f'{max(sp_d):.2f}')} to {m_(f'{min(sp_d):.2f}')}; animal share {m_(f'{max(sp_a):.2f}')} to {m_(f'{min(sp_a):.2f}')}"])
    # grams, retest, effort, valid subset
    grams = {}
    for r in R:
        i = key.get((r["participant_id"], r["date"], r["meal_type"]))
        if i and r["total_consumed_g"]:
            grams[i] = float(r["total_consumed_g"])
    parts = []
    for m in MODELS:
        r = abl_load(f"dual_simple_{KEY[m]}", "intake-all")
        its = [i for i in grams if i in r and r[i].get("mass_g") and grams[i] > 0]
        ae = [abs(r[i]["mass_g"] - grams[i]) for i in its]; tot = sum(grams[i] for i in its)
        parts.append(f"{m} {st.mean(ae):.0f} g, {sum(ae) / tot * 100:.1f}%, {s1((sum(r[i]['mass_g'] for i in its) - tot) / tot * 100)}%")
    block("APPF_GRAMS_TEXT", ["**Grams eaten from (3a)** (MAE g; error relative to mean true grams; bias): " + "; ".join(parts) + "."])
    pilot_items = sorted(l["item"] for l in subset("pilot", lab_list))
    parts = []; ranges = []; cvs = []; pds = []
    eff = []; eff_delta = []
    for m, (_, s3, _) in MODELS.items():
        runs = [abl_load(s3, "intake-pilot"), abl_load(s3, "intake-pilot-r1"), abl_load(s3, "intake-pilot-r2")]
        ok = [i for i in pilot_items if all(r.get(i, {}).get("est") for r in runs)]
        maes = [sum(abs(r[i]["est"] - LAB[i]["kcal"]) for i in ok) / sum(LAB[i]["kcal"] for i in ok) * 100 for r in runs]
        cv = st.median(st.stdev([r[i]["est"] for r in runs]) / st.mean([r[i]["est"] for r in runs]) * 100 for i in ok)
        pd = st.mean(abs(r_[i]["est"] - r2[i]["est"]) / LAB[i]["kcal"] * 100 for i in ok for a, r_ in enumerate(runs) for r2 in runs[a + 1:])
        ranges.append(max(maes) - min(maes)); cvs.append(cv); pds.append(pd)
        parts.append(f"{m} {f1(maes[0])} / {f1(maes[1])} / {f1(maes[2])}; {cv:.1f}%; {pd:.1f}%" + ("" if len(ok) == len(pilot_items) else f" ({len(ok)} meals parsed in all three)"))
        hi = abl_load(f"dual_high_{KEY[m]}", "intake-pilot")
        ok2 = [i for i in pilot_items if hi.get(i, {}).get("est") and all(r.get(i, {}).get("est") for r in runs)]
        ml = st.mean(sum(abs(r[i]["est"] - LAB[i]["kcal"]) for i in ok2) / sum(LAB[i]["kcal"] for i in ok2) * 100 for r in runs)
        mh = sum(abs(hi[i]["est"] - LAB[i]["kcal"]) for i in ok2) / sum(LAB[i]["kcal"] for i in ok2) * 100
        bl = st.mean((sum(r[i]["est"] for i in ok2) - sum(LAB[i]["kcal"] for i in ok2)) / sum(LAB[i]["kcal"] for i in ok2) * 100 for r in runs)
        bh = (sum(hi[i]["est"] for i in ok2) - sum(LAB[i]["kcal"] for i in ok2)) / sum(LAB[i]["kcal"] for i in ok2) * 100
        cl = json.load(open(os.path.join(ROOT, "runs", s3, "intake-pilot-r1.json")))["metrics"]
        ch = json.load(open(os.path.join(ROOT, "runs", f"dual_high_{KEY[m]}", "intake-pilot.json")))["metrics"]
        ratio = (ch["usd"] / max(ch["calls"], 1)) / (cl["usd"] / max(cl["calls"], 1))
        eff.append(f"{m} {f1(ml)} → {f1(mh)}; {s1(bl)} → {s1(bh)}; ×{ratio:.1f}")
        eff_delta.append((m, mh - ml, ratio))
    block("APPF_RETEST_TEXT", ["**Test–retest, condition (3), 100 pilot meals, three calls** (MAE% per call; median per-meal CV; mean absolute difference between two calls as % of truth): " + ". ".join(parts) + "."])
    block("RETEST_RANGES", [f"max within-model MAE% range {f1(max(ranges))}; median CV {min(cvs):.1f}–{max(cvs):.1f}%; pairwise difference {min(pds):.1f}–{max(pds):.1f}%"])
    block("APPF_EFFORT_TEXT", ["**Reasoning effort, condition (3), same 100 meals** (MAE% low, mean of three calls → high; bias low → high; cost per meal, high relative to low): " + ". ".join(eff) + "."])
    block("EFFORT_DELTAS", ["; ".join(f"{m} {s1(d)} (×{r:.1f})" for m, d, r in eff_delta)])
    parts = []
    for m in MODELS:
        ok = set(OK[m][0]) & set(OK[m][1]) & set(OK[m][2]); its = [i for i in ITS if i in ok]
        es, ed, eb = E[m]
        parts.append(f"{m} (n = {len(its)}) {f1(mae(es, its))} / {f1(mae(eb, its))} / {f1(mae(ed, its))}")
    block("APPF_VALID_TEXT", ["**Valid-output subset** (meals parsed in all three conditions for that model): MAE% before / subtraction / both — " + "; ".join(parts) + "."])
    # failures per model/condition
    block("FAILS", ["; ".join(f"{m} {NF[m][0]}/{NF[m][2]}/{NF[m][1]} (before/subtraction/both)" for m in MODELS)])
    # eaten fraction read from the photos
    parts = []
    for m in MODELS:
        ok = OK[m][1]
        pairs = [(ok[i]["served_kcal"], ok[i]["leftover_kcal"], LAB[i]["served_kcal"], LAB[i]["kcal"]) for i in KNOWN if i in ok and ok[i].get("served_kcal") and ok[i].get("leftover_kcal") is not None]
        sv = (sum(p[0] for p in pairs) - sum(p[2] for p in pairs)) / sum(p[2] for p in pairs) * 100
        tl = sum(p[2] - p[3] for p in pairs); el = sum(p[1] for p in pairs)
        parts.append(f"{m} served {s1(sv)}%, leftover {s0((el - tl) / tl * 100)}%")
    block("SERVED_LEFTOVER_TEXT", ["Both-photos reading of served energy and of energy left (total estimate vs total truth, meals with served defined): " + "; ".join(parts) + "."])


if __name__ == "__main__":
    print(f"<<MODELS>>\n{', '.join(MODELS)}\n")
    table2(); table3(); table4(); table5(); table7(); appd(); appf()
