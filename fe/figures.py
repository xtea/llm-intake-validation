"""Paper figures (static PDF for LaTeX). python3 -m fe.figures <outdir>"""
import json, math, os, statistics as st, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fe.llm import ROOT
from fe.ablation import MODELS, rows, fit, apply, invert

C = {"Direct": "#2a78d6", "Direct + cal": "#eb6834", "A without cal": "#1baf7a", "Harness A": "#eda100"}
M = {"Direct": "o", "Direct + cal": "s", "A without cal": "^", "Harness A": "D"}
INK, MUTED, GRID = "#1f1f1e", "#6b6b66", "#e4e3df"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 9,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})


def labels(split):
    return {l["item"]: l["kcal"] for l in json.load(open(os.path.join(ROOT, "data", "labels", f"{split}.json")))}


def systems(model, split):
    b0, b2, a, (ca, wa) = MODELS[model]
    out = {}
    e = rows(b0, f"{split}-all")
    f0 = rows(b0, "search-300-f0")
    if e:
        out["Direct"] = {i: r["est"] for i, r in e.items()}
        if f0:
            Cc, W = fit(list(f0.values()))
            out["Direct + cal"] = {i: apply(Cc, W, r["est"]) for i, r in e.items()}
    ea = rows(a, f"{split}-all")
    if ea:
        out["A without cal"] = {i: invert(ca, wa, r["est"]) for i, r in ea.items()}
        out["Harness A"] = {i: r["est"] for i, r in ea.items()}
    return out


def mae(est, lab):
    its = [i for i in est if i in lab]
    return sum(abs(est[i] - lab[i]) for i in its) / sum(lab[i] for i in its) * 100


def fig_ablation(out, splits):
    titles = {"test": "Nutrition5k test (in distribution)", "nvreal": "NutritionVerse-Real (OOD)", "acetada": "ACETADA (OOD)"}
    models = list(MODELS)
    fig, axes = plt.subplots(1, len(splits), figsize=(2.35 * len(splits) + 0.9, 2.9), sharey=True)
    for ax, split in zip(axes, splits):
        lab = labels(split)
        for y, model in enumerate(models):
            sy = systems(model, split)
            xs = [mae(e, lab) for e in sy.values()]
            if xs:
                ax.plot([min(xs), max(xs)], [y, y], color=GRID, lw=2, zorder=1)
            for k, e in sy.items():
                ax.scatter(mae(e, lab), y, s=30, marker=M[k], color=C[k], edgecolor="white", linewidth=0.8, zorder=3, label=k)
        ax.set_title(titles[split], fontsize=9, color=INK)
        ax.set_xlabel("MAE (% of mean energy)")
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(models)))
    axes[0].set_yticklabels(models)
    axes[0].invert_yaxis()
    h, l = axes[0].get_legend_handles_labels()
    uniq = dict(zip(l, h))
    fig.legend(uniq.values(), uniq.keys(), loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.55, -0.02))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(out, "fig_ablation.pdf"))
    fig.savefig(os.path.join(out, "fig_ablation.png"), dpi=160)


def fig_ratio(out, splits):
    """median estimate/label ratio by label-energy bin, Haiku: Direct, Direct + cal, A without cal, Harness A"""
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    bins = [30, 100, 200, 300, 450, 650, 900, 1300, 3000]
    pooled = {k: [] for k in ("Direct", "Direct + cal", "A without cal", "Harness A")}
    for split in splits:
        lab = labels(split)
        sy = systems("Haiku 5.5", split)
        for k in pooled:
            pooled[k] += [(lab[i], v / lab[i]) for i, v in sy.get(k, {}).items() if i in lab and lab[i] > 0]
    for k, pts in pooled.items():
        xs, ys = [], []
        for lo, hi in zip(bins, bins[1:]):
            r = [q for y, q in pts if lo <= y < hi]
            if len(r) >= 15:
                xs.append(math.sqrt(lo * hi))
                ys.append(st.median(r))
        ax.plot(xs, ys, marker=M[k], color=C[k], lw=2, ms=5, label=k, markeredgecolor="white")
    ax.axhline(1.0, color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.set_xscale("log")
    ax.set_xticks([50, 100, 200, 500, 1000, 2000])
    ax.set_xticklabels(["50", "100", "200", "500", "1000", "2000"])
    ax.set_xlabel("True energy of the dish (kcal, log scale)")
    ax.set_ylabel("Median estimate / truth")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Haiku 5.5, pooled over " + ", ".join(splits), fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig_ratio.pdf"))
    fig.savefig(os.path.join(out, "fig_ratio.png"), dpi=160)


def fig_ba(out):
    """day-level Bland-Altman on ACETADA feeding days (post hoc), same layout as the trial's own recall comparison."""
    from fe import clinical as cl
    lab = cl.labels("acetada")
    dd = cl.days(lab)
    sy = cl.systems("acetada")
    panels = [("Haiku 5.5", "Harness A"), ("Haiku 5.5", "Direct"), ("gpt-6.1-sol", "Direct"), ("Opus 5.5", "Plate")]
    names = {"gpt-6.1-sol": "GPT-6.1 sol", "Plate": "Plate-as-ruler"}
    fig, axes = plt.subplots(1, 4, figsize=(9.4, 2.6), sharey=True)
    for ax, (m, k) in zip(axes, panels):
        est = sy[(m, k)]
        xs, ys = [], []
        for its in dd.values():
            t = sum(lab[i]["kcal"] for i in its)
            xs.append(t)
            ys.append((sum(est[i] for i in its) - t) / t * 100)
        mu, sd = st.mean(ys), st.stdev(ys)
        ax.scatter(xs, ys, s=10, color="#2a78d6", alpha=0.7, edgecolor="white", linewidth=0.4)
        ax.axhline(0, color=MUTED, lw=0.8, ls=(0, (3, 3)))
        for v, lw in ((mu, 1.4), (mu - 1.96 * sd, 0.9), (mu + 1.96 * sd, 0.9)):
            ax.axhline(v, color="#eb6834", lw=lw)
        ax.set_title(f"{names.get(m, m)}, {names.get(k, k)}", fontsize=8.5, color=INK)
        ax.text(0.97, 0.96, f"mean {mu:+.0f}%\nLoA {mu - 1.96 * sd:+.0f} to {mu + 1.96 * sd:+.0f}%", transform=ax.transAxes,
                ha="right", va="top", fontsize=7.5, color=INK)
        ax.set_xlabel("True energy served per day (kcal)")
        ax.grid(axis="y", color=GRID, lw=0.6)
    axes[0].set_ylabel("Day error (% of truth)")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig_ba.pdf"))
    fig.savefig(os.path.join(out, "fig_ba.png"), dpi=160)


def fig_intake_ba(out):
    """Addendum H: day-level Bland-Altman of consumed energy, both photos, all models; preset limits only (no recall overlay)."""
    from fe import intake_report as ir
    dd = ir.days()
    n = len(ir.MODELS)
    cols = 3 if n <= 6 else 4
    rows_ = -(-n // cols)
    fig, axes = plt.subplots(rows_, cols, figsize=(2.4 * cols, 2.3 * rows_), sharex=True, sharey=True, squeeze=False)
    for ax in list(axes.flat)[n:]:
        ax.set_visible(False)
    for ax, (m, (_, d, _)) in zip(axes.flat, ir.MODELS.items()):
        est = ir.scored(d)[0]
        xs, ys = [], []
        for its in dd.values():
            t = sum(ir.LAB[i]["kcal"] for i in its)
            xs.append(t)
            ys.append((sum(est[i] for i in its) - t) / t * 100)
        mu, sd = st.mean(ys), st.stdev(ys)
        for v in (-30, 30):
            ax.axhline(v, color=MUTED, lw=0.8, ls=(0, (1, 2)))
        for v in (-10, 10):
            ax.axhline(v, color=GRID, lw=0.8)
        ax.axhline(0, color=MUTED, lw=0.6)
        ax.scatter(xs, ys, s=9, color="#2a78d6", alpha=0.75, edgecolor="white", linewidth=0.4, zorder=3)
        ax.axhline(mu, color="#eb6834", lw=1.4, zorder=4)
        for v in (mu - 1.96 * sd, mu + 1.96 * sd):
            ax.axhline(v, color="#eb6834", lw=0.9, ls=(0, (4, 2)), zorder=4)
        # local-linear smoother (tricube weights, span 0.6), the usual LOESS reading of a Bland-Altman plot
        xs_a, ys_a = np.array(xs), np.array(ys)
        grid = np.linspace(np.percentile(xs_a, 2), np.percentile(xs_a, 98), 60)
        h = 0.6 * (xs_a.max() - xs_a.min()) / 2
        sm = []
        for g in grid:
            w = np.clip(1 - (np.abs(xs_a - g) / h) ** 3, 0, None) ** 3
            A = np.vstack([np.ones_like(xs_a), xs_a - g]).T
            beta = np.linalg.lstsq(A * w[:, None] ** 0.5, ys_a * w ** 0.5, rcond=None)[0]
            sm.append(beta[0])
        ax.plot(grid, sm, color=INK, lw=1.0, ls=(0, (2, 1.5)), zorder=5)
        ax.set_title(m, fontsize=8.5, color=INK)
        ax.text(0.97, 0.96, f"mean {mu:+.1f}%\nLoA {mu - 1.96 * sd:+.0f} to {mu + 1.96 * sd:+.0f}%", transform=ax.transAxes,
                ha="right", va="top", fontsize=7, color=INK)
        ax.set_ylim(-80, 100)
    for k, ax in enumerate(axes.flat):
        if k >= n - cols:
            ax.set_xlabel("True energy eaten per day (kcal)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Day error (% of truth)")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig_intake_ba.pdf"))
    fig.savefig(os.path.join(out, "fig_intake_ba.png"), dpi=160)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "results")
    os.makedirs(out, exist_ok=True)
    sp = ["test", "nvreal"] + (["acetada"] if os.path.exists(os.path.join(ROOT, "runs", "compA_v4", "acetada-all.json")) else [])
    fig_ablation(out, sp)
    fig_ratio(out, sp)
    if "acetada" in sp:
        fig_ba(out)
    if os.path.exists(os.path.join(ROOT, "runs", "dual_direct_opus", "intake-all.json")):
        fig_intake_ba(out)
    print("ok", sp)
